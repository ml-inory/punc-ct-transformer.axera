#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

#include "punctuation_runner.h"

static void print_usage(const char* prog) {
    std::cerr << "Usage: " << prog << " [OPTIONS] [TEXT]\n"
              << "\n"
              << "Sherpa Punctuation Prediction on AX650 NPU.\n"
              << "\n"
              << "Options:\n"
              << "  -m, --model  PATH   Model path (default: ../models/model.axmodel)\n"
              << "  -t, --tokens PATH   Tokens path (default: ../models/tokens.json)\n"
              << "  -h, --help          Show this help\n"
              << "\n"
              << "If TEXT is provided, runs on that text.\n"
              << "Otherwise, runs built-in demo texts.\n";
}

static bool file_exists(const std::string& path) {
    std::ifstream f(path);
    return f.good();
}

int main(int argc, char* argv[]) {
    std::string model_path;
    std::string vocab_path;
    std::string text;

    // Parse args
    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "-h" || arg == "--help") {
            print_usage(argv[0]);
            return 0;
        } else if ((arg == "-m" || arg == "--model") && i + 1 < argc) {
            model_path = argv[++i];
        } else if ((arg == "-t" || arg == "--tokens") && i + 1 < argc) {
            vocab_path = argv[++i];
        } else if (arg[0] != '-') {
            if (!text.empty()) text += " ";
            text += arg;
        } else {
            std::cerr << "Unknown option: " << arg << "\n";
            print_usage(argv[0]);
            return 1;
        }
    }

    // Smart defaults
    if (model_path.empty()) {
        const char* candidates[] = {
            "../models/model.axmodel",
            "../../models/model.axmodel",
        };
        for (auto c : candidates) {
            if (file_exists(c)) { model_path = c; break; }
        }
    }
    if (vocab_path.empty()) {
        const char* candidates[] = {
            "../models/tokens.json",
            "../../models/tokens.json",
        };
        for (auto c : candidates) {
            if (file_exists(c)) { vocab_path = c; break; }
        }
    }

    if (model_path.empty() || vocab_path.empty()) {
        std::cerr << "ERROR: model or tokens not found.\n";
        std::cerr << "  Use -m and -t to specify paths.\n";
        return 1;
    }

    std::cerr << "Model:  " << model_path << std::endl;
    std::cerr << "Vocab:  " << vocab_path << std::endl;

    // Init
    PunctuationRunner runner;
    if (runner.LoadVocab(vocab_path) != 0) {
        std::cerr << "Failed to load vocabulary" << std::endl;
        return 1;
    }
    std::cerr << "Vocab size: " << runner.VocabSize() << std::endl;

    int ret = runner.Init(model_path);
    if (ret != 0) {
        std::cerr << "AX Engine init failed (requires AX650 hardware)." << std::endl;
        return ret;
    }

    // Run
    std::vector<std::string> texts;
    if (!text.empty()) {
        texts.push_back(text);
    } else {
        texts = {
            "你好吗how are you我很好谢谢",
            "今天天气真不错我们出去走走吧",
            "人工智能技术正在改变我们的生活方式"
            "明天下午三点在公司会议室开会请准时参加"
            "他是一名优秀的工程师工作认真负责"
            "北京是中国的首都拥有悠久的历史文化",
        };
    }

    for (const auto& t : texts) {
        std::cout << "Input:  " << t << std::endl;
        std::string result = runner.Run(t);
        std::cout << "Output: " << result << std::endl << std::endl;
    }

    return 0;
}
