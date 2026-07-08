#ifndef PUNCTUATION_RUNNER_H
#define PUNCTUATION_RUNNER_H

#include <cstdint>
#include <string>
#include <vector>

#include "ax_engine_type.h"

/// PunctuationRunner: loads sherpa punct CT Transformer AXMODEL and
/// adds punctuation to Chinese text using AX Engine native API.
///
/// Model inputs:  int32[1, 64]   token IDs (padded)
/// Model outputs: float32[1, 64, 6]  logits for 6 classes
class PunctuationRunner {
public:
    static constexpr int kInputLen = 64;
    static constexpr int kNumClasses = 6;
    static constexpr int kMaxIOBuffers = 4;

    PunctuationRunner();
    ~PunctuationRunner();

    /// Initialize with model path.
    /// Returns 0 on success, non-zero on failure.
    int Init(const std::string& model_path);

    /// Load vocabulary from tokens.json (list of strings).
    int LoadVocab(const std::string& vocab_path);

    /// Run punctuation prediction on raw text.
    /// Returns text with punctuation inserted.
    std::string Run(const std::string& text);

    /// Get vocabulary size.
    int VocabSize() const { return static_cast<int>(vocab_.size()); }

private:
    /// Tokenize text into token IDs.
    std::vector<int32_t> Tokenize(const std::string& text);

    /// Decode logits to punctuation string.
    std::string Decode(const float* logits, int num_tokens,
                       const std::vector<int32_t>& token_ids);

    // AX Engine state
    AX_ENGINE_HANDLE engine_ = nullptr;
    AX_ENGINE_IO_T io_;
    AX_ENGINE_IO_BUFFER_T in_bufs_[kMaxIOBuffers];
    AX_ENGINE_IO_BUFFER_T out_bufs_[kMaxIOBuffers];
    AX_U32 n_inputs_ = 0;
    AX_U32 n_outputs_ = 0;
    AX_U32 input_size_ = 0;
    AX_U32 output_size_ = 0;

    std::vector<std::string> vocab_;
    int unk_id_ = 0;
    bool initialized_ = false;
};

#endif // PUNCTUATION_RUNNER_H
