#include <cstring>
#include <iostream>
#include <string>

#include "punctuation_runner.h"

int main(int argc, char* argv[]) {
    std::string model_path;
    std::string vocab_path;
    std::string text;

    if (argc >= 3) {
        model_path = argv[1];
        vocab_path = argv[2];
    } else {
        model_path = "../models/model.axmodel";
        vocab_path = "../models/tokens.json";
    }

    std::cerr << "Model:  " << model_path << std::endl;
    std::cerr << "Vocab:  " << vocab_path << std::endl;

    PunctuationRunner runner;
    if (runner.LoadVocab(vocab_path) != 0) {
        std::cerr << "Failed to load vocabulary" << std::endl;
        return 1;
    }
    std::cerr << "Vocab size: " << runner.VocabSize() << std::endl;

    // Init with model (AX Engine on hardware)
    int ret = runner.Init(model_path);
    if (ret != 0) {
        std::cerr << "AX Engine init failed (expected on non-AX650 host). "
                  << "This binary must run on AX650 hardware." << std::endl;
        return ret;
    }

    std::vector<std::string> texts;
    if (argc >= 4) {
        texts.push_back(argv[3]);
    } else {
        texts = {
            "你好吗how are you我很好谢谢",
            "今天天气真不错我们出去走走吧",
            // Long text: auto-sliding-window test
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
