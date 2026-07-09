#include "punctuation_runner.h"

#include <algorithm>
#include <cmath>
#include <cstring>
#include <fstream>
#include <iostream>
#include <sstream>
#include <unordered_map>

// Native AX Engine API
#include "ax_engine_type.h"
#include "ax_engine_api.h"
#include "ax_sys_api.h"

// ---------------------------------------------------------------------------
// JSON helper: minimal list-of-strings parser for tokens.json
// ---------------------------------------------------------------------------
static std::vector<std::string> ParseTokenList(const std::string& path) {
    std::ifstream f(path);
    if (!f.is_open()) {
        std::cerr << "Failed to open " << path << std::endl;
        return {};
    }
    std::string content((std::istreambuf_iterator<char>(f)),
                        std::istreambuf_iterator<char>());

    std::vector<std::string> tokens;
    size_t pos = content.find('[');
    if (pos == std::string::npos) return tokens;
    pos++;

    while (pos < content.size()) {
        while (pos < content.size() && std::isspace(content[pos])) pos++;
        if (content[pos] == ']') break;
        if (content[pos] == ',') { pos++; continue; }

        if (content[pos] == '"') {
            pos++;
            std::string tok;
            while (pos < content.size() && content[pos] != '"') {
                if (content[pos] == '\\' && pos + 1 < content.size()) {
                    pos++;
                    if (content[pos] == 'u') { pos += 5; continue; }
                }
                tok += content[pos++];
            }
            tokens.push_back(tok);
            if (pos < content.size()) pos++;
        } else {
            pos++;
        }
    }
    return tokens;
}

// ---------------------------------------------------------------------------
// Tokenizer helpers
// ---------------------------------------------------------------------------
static bool IsMultiByte(char c) {
    return (static_cast<unsigned char>(c) > 127);
}

static std::vector<int32_t> TokenizeImpl(
    const std::string& text,
    const std::unordered_map<std::string, int>& token2id,
    int unk_id)
{
    std::vector<std::string> words;
    std::string cur;
    for (char c : text) {
        if (std::isspace(c)) {
            if (!cur.empty()) { words.push_back(cur); cur.clear(); }
        } else {
            cur += c;
        }
    }
    if (!cur.empty()) words.push_back(cur);

    std::vector<std::string> segments;
    for (const auto& w : words) {
        std::string s;
        for (size_t i = 0; i < w.size(); i++) {
            char c = w[i];
            if (IsMultiByte(c)) {
                if (s.empty()) {
                    s = std::string(1, c);
                } else if (IsMultiByte(s.back())) {
                    s += c;
                } else {
                    segments.push_back(s);
                    s = std::string(1, c);
                }
            } else {
                if (s.empty()) {
                    s = std::string(1, c);
                } else if (IsMultiByte(s.back())) {
                    segments.push_back(s);
                    s = std::string(1, c);
                } else {
                    s += c;
                }
            }
        }
        if (!s.empty()) segments.push_back(s);
    }

    std::vector<int32_t> ids;
    for (const auto& seg : segments) {
        if (IsMultiByte(seg[0])) {
            for (size_t j = 0; j < seg.size();) {
                int clen = 1;
                unsigned char u = seg[j];
                if ((u & 0xE0) == 0xC0) clen = 2;
                else if ((u & 0xF0) == 0xE0) clen = 3;
                else if ((u & 0xF8) == 0xF0) clen = 4;
                std::string ch = seg.substr(j, clen);
                auto it = token2id.find(ch);
                ids.push_back(it != token2id.end() ? it->second : unk_id);
                j += clen;
            }
        } else {
            auto it = token2id.find(seg);
            ids.push_back(it != token2id.end() ? it->second : unk_id);
        }
    }
    return ids;
}

// ---------------------------------------------------------------------------
// Decode logits to punctuated text
// ---------------------------------------------------------------------------
static std::string DecodeImpl(
    const float* logits, int num_tokens,
    const std::vector<int32_t>& token_ids,
    const std::vector<std::string>& vocab, int unk_id)
{
    static const int kCommaId = 2;
    static const int kDotId = 3;
    static const int kQuestId = 4;
    static const int kIgnoreId = 1;
    static const int kNumClasses = 6;
    static const char* kMarks[] = {"", "", "\xEF\xBC\x8C", "\xE3\x80\x82",
                                    "\xEF\xBC\x9F", "\xE3\x80\x81"};

    std::vector<int> out(num_tokens);
    for (int t = 0; t < num_tokens; t++) {
        int best = 0;
        float best_val = logits[t * kNumClasses];
        for (int c = 1; c < kNumClasses; c++) {
            float v = logits[t * kNumClasses + c];
            if (v > best_val) { best_val = v; best = c; }
        }
        out[t] = best;
    }

    const int kSegSize = 20;
    const int kMaxLen = 200;
    int num_segs = (num_tokens + kSegSize - 1) / kSegSize;
    std::vector<int> punctuations;
    int last = -1;

    for (int i = 0; i < num_segs; i++) {
        int start = i * kSegSize;
        int end = std::min(start + kSegSize, num_tokens);
        if (last != -1) start = last;

        int dot_idx = -1, comma_idx = -1;
        for (int k = end - 1; k > 1; k--) {
            if (out[k] == kDotId || out[k] == kQuestId) {
                dot_idx = k; break;
            }
            if (comma_idx == -1 && out[k] == kCommaId) comma_idx = k;
        }
        if (dot_idx == -1 && num_tokens >= kMaxLen && comma_idx != -1) {
            dot_idx = comma_idx;
            out[dot_idx] = kDotId;
        }
        if (dot_idx == -1) {
            if (last == -1) last = start;
            if (i == num_segs - 1) dot_idx = end - 1;
        } else {
            last = start + dot_idx + 1;
        }
        if (dot_idx != -1) {
            for (int j = 0; j <= dot_idx && start + j < num_tokens; j++) {
                punctuations.push_back(out[start + j]);
            }
        }
    }

    std::string result;
    int p_count = static_cast<int>(punctuations.size());
    for (int j = 0; j < p_count && j < (int)token_ids.size(); j++) {
        int tid = token_ids[j];
        const char* token = (tid >= 0 && tid < (int)vocab.size()) ?
                            vocab[tid].c_str() : "<unk>";
        // Insert space between consecutive ASCII (single-byte) tokens
        if (!result.empty() && token[0] != '\0') {
            bool prev_ascii = (static_cast<unsigned char>(result.back()) <= 127);
            bool cur_ascii = (static_cast<unsigned char>(token[0]) <= 127);
            if (prev_ascii && cur_ascii) result += ' ';
        }
        result += token;
        int p = punctuations[j];
        if (p != kIgnoreId && p >= 0 && p < 6 && kMarks[p][0] != '\0') {
            result += kMarks[p];
        }
    }
    return result;
}

// ===================================================================
// PunctuationRunner — Native AX Engine implementation
// ===================================================================

PunctuationRunner::PunctuationRunner() = default;

PunctuationRunner::~PunctuationRunner() {
    if (initialized_) {
        for (AX_U32 i = 0; i < n_inputs_; i++) {
            if (in_bufs_[i].phyAddr)
                AX_SYS_MemFree(in_bufs_[i].phyAddr, in_bufs_[i].pVirAddr);
        }
        for (AX_U32 i = 0; i < n_outputs_; i++) {
            if (out_bufs_[i].phyAddr)
                AX_SYS_MemFree(out_bufs_[i].phyAddr, out_bufs_[i].pVirAddr);
        }
        if (engine_) {
            AX_ENGINE_DestroyHandle(engine_);
            AX_ENGINE_Deinit();
        }
        AX_SYS_Deinit();
    }
}

int PunctuationRunner::Init(const std::string& model_path) {
    // 1. Init AX system
    AX_S32 ret = AX_SYS_Init();
    if (ret != 0) {
        std::cerr << "AX_SYS_Init failed: 0x" << std::hex << ret << std::dec << std::endl;
        return -1;
    }

    // 2. Init AX engine
    AX_ENGINE_NPU_ATTR_T npu_attr;
    memset(&npu_attr, 0, sizeof(npu_attr));
    npu_attr.eHardMode = AX_ENGINE_VIRTUAL_NPU_DISABLE;
    ret = AX_ENGINE_Init(&npu_attr);
    if (ret != 0) {
        std::cerr << "AX_ENGINE_Init failed: 0x" << std::hex << ret << std::dec << std::endl;
        AX_SYS_Deinit();
        return -2;
    }

    // 3. Read model file
    FILE* fm = fopen(model_path.c_str(), "rb");
    if (!fm) {
        std::cerr << "Cannot open model: " << model_path << std::endl;
        AX_ENGINE_Deinit(); AX_SYS_Deinit();
        return -3;
    }
    fseek(fm, 0, SEEK_END);
    size_t msize = ftell(fm);
    fseek(fm, 0, SEEK_SET);
    void* mdata = malloc(msize);
    fread(mdata, 1, msize, fm);
    fclose(fm);

    // 4. Create handle
    ret = AX_ENGINE_CreateHandle(&engine_, mdata, (AX_U32)msize);
    free(mdata);
    if (ret != 0 || !engine_) {
        std::cerr << "AX_ENGINE_CreateHandle failed: 0x" << std::hex << ret << std::dec << std::endl;
        AX_ENGINE_Deinit(); AX_SYS_Deinit();
        return -4;
    }

    // 5. Create context
    ret = AX_ENGINE_CreateContext(engine_);
    if (ret != 0) {
        std::cerr << "AX_ENGINE_CreateContext failed: 0x" << std::hex << ret << std::dec << std::endl;
        AX_ENGINE_DestroyHandle(engine_); engine_ = nullptr;
        AX_ENGINE_Deinit(); AX_SYS_Deinit();
        return -5;
    }

    // 6. Get IO info
    AX_ENGINE_IO_INFO_T* io_info = nullptr;
    ret = AX_ENGINE_GetIOInfo(engine_, &io_info);
    if (ret != 0 || !io_info) {
        std::cerr << "AX_ENGINE_GetIOInfo failed: 0x" << std::hex << ret << std::dec << std::endl;
        AX_ENGINE_DestroyHandle(engine_); engine_ = nullptr;
        AX_ENGINE_Deinit(); AX_SYS_Deinit();
        return -6;
    }

    n_inputs_ = io_info->nInputSize;
    n_outputs_ = io_info->nOutputSize;
    input_size_ = io_info->pInputs[0].nSize;
    output_size_ = io_info->pOutputs[0].nSize;

    // 7. Allocate IO buffers (physical memory via AX_SYS_MemAlloc)
    for (AX_U32 i = 0; i < n_inputs_; i++) {
        AX_U32 sz = io_info->pInputs[i].nSize;
        AX_U32 alloc_sz = (sz + 0xFFF) & ~0xFFF;
        ret = AX_SYS_MemAlloc((AX_U64*)&in_bufs_[i].phyAddr,
                              &in_bufs_[i].pVirAddr, alloc_sz, 0x100, NULL);
        if (ret != 0) {
            // Fallback to virtual memory
            in_bufs_[i].phyAddr = 0;
            in_bufs_[i].pVirAddr = malloc(sz);
            alloc_sz = sz;
        }
        in_bufs_[i].nSize = alloc_sz;
        memset(in_bufs_[i].pVirAddr, 0, sz);
    }

    for (AX_U32 i = 0; i < n_outputs_; i++) {
        AX_U32 sz = io_info->pOutputs[i].nSize;
        AX_U32 alloc_sz = (sz + 0xFFF) & ~0xFFF;
        ret = AX_SYS_MemAlloc((AX_U64*)&out_bufs_[i].phyAddr,
                              &out_bufs_[i].pVirAddr, alloc_sz, 0x100, NULL);
        if (ret != 0) {
            out_bufs_[i].phyAddr = 0;
            out_bufs_[i].pVirAddr = malloc(sz);
            alloc_sz = sz;
        }
        out_bufs_[i].nSize = alloc_sz;
    }

    // 8. Build IO struct
    memset(&io_, 0, sizeof(io_));
    io_.nInputSize = n_inputs_;
    io_.pInputs = in_bufs_;
    io_.nOutputSize = n_outputs_;
    io_.pOutputs = out_bufs_;

    initialized_ = true;
    return 0;
}

int PunctuationRunner::LoadVocab(const std::string& vocab_path) {
    vocab_ = ParseTokenList(vocab_path);
    if (vocab_.empty()) {
        std::cerr << "Failed to load vocabulary from " << vocab_path << std::endl;
        return -1;
    }
    for (size_t i = 0; i < vocab_.size(); i++) {
        if (vocab_[i] == "<unk>") { unk_id_ = static_cast<int>(i); break; }
    }
    return 0;
}

std::vector<int32_t> PunctuationRunner::Tokenize(const std::string& text) {
    std::unordered_map<std::string, int> token2id;
    for (int i = 0; i < static_cast<int>(vocab_.size()); i++) {
        token2id[vocab_[i]] = i;
    }
    return TokenizeImpl(text, token2id, unk_id_);
}

std::string PunctuationRunner::Decode(
    const float* logits, int num_tokens,
    const std::vector<int32_t>& token_ids)
{
    return DecodeImpl(logits, num_tokens, token_ids, vocab_, unk_id_);
}

std::string PunctuationRunner::Run(const std::string& text) {
    if (!initialized_) return "";

    auto token_ids = Tokenize(text);
    if (token_ids.empty()) return text;

    int total_tokens = static_cast<int>(token_ids.size());
    const int kStride = 60;  // overlap = kInputLen - kStride = 4

    // Short text: single inference
    if (total_tokens <= kInputLen) {
        std::vector<int32_t> input(kInputLen, 0);
        for (int i = 0; i < total_tokens; i++) input[i] = token_ids[i];
        memcpy(in_bufs_[0].pVirAddr, input.data(), kInputLen * sizeof(int32_t));

        AX_S32 ret = AX_ENGINE_RunSync(engine_, &io_);
        if (ret != 0) {
            std::cerr << "AX_ENGINE_RunSync failed: 0x" << std::hex << ret << std::dec << std::endl;
            return text;
        }
        const float* logits = (const float*)out_bufs_[0].pVirAddr;
        return Decode(logits, total_tokens, token_ids);
    }

    // Long text: sliding window
    // Output buffer for all per-token logits: total_tokens x kNumClasses
    std::vector<float> all_logits(total_tokens * kNumClasses, 0.0f);

    for (int start = 0; start < total_tokens; start += kStride) {
        int end = std::min(start + kInputLen, total_tokens);
        int chunk_len = end - start;

        // Prepare padded input
        std::vector<int32_t> input(kInputLen, 0);
        for (int i = 0; i < chunk_len; i++) input[i] = token_ids[start + i];
        memcpy(in_bufs_[0].pVirAddr, input.data(), kInputLen * sizeof(int32_t));

        // Run inference
        AX_S32 ret = AX_ENGINE_RunSync(engine_, &io_);
        if (ret != 0) {
            std::cerr << "AX_ENGINE_RunSync failed: 0x" << std::hex << ret << std::dec << std::endl;
            return text;
        }

        const float* logits = (const float*)out_bufs_[0].pVirAddr;

        // Copy logits to output buffer
        if (start == 0) {
            // First window: keep all token logits
            for (int t = 0; t < chunk_len; t++) {
                for (int c = 0; c < kNumClasses; c++) {
                    all_logits[t * kNumClasses + c] = logits[t * kNumClasses + c];
                }
            }
        } else {
            // Subsequent windows: skip overlap, keep only new tokens
            int overlap = kInputLen - kStride;
            for (int t = overlap; t < chunk_len; t++) {
                int global_t = start + t;
                if (global_t >= total_tokens) break;
                for (int c = 0; c < kNumClasses; c++) {
                    all_logits[global_t * kNumClasses + c] = logits[t * kNumClasses + c];
                }
            }
        }
    }

    return Decode(all_logits.data(), total_tokens, token_ids);
}
