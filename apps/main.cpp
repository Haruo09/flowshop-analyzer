#include "flowshop_analyzer/solver_api.h"

#include <fstream>
#include <iostream>
#include <string>
#include <vector>

static std::string trim(const std::string &str) {
    size_t first = str.find_first_not_of(" \t\r\n");
    if (first == std::string::npos)
        return "";
    size_t last = str.find_last_not_of(" \t\r\n");
    return str.substr(first, last - first + 1);
}

int main() {
    std::ifstream file("instancias.txt");
    if (!file.is_open()) {
        std::cerr << "Error opening instancias.txt\n";
        return 1;
    }

    std::string line;
    int total_instances = 0;

    while (std::getline(file, line)) {
        std::string clean_line = trim(line);
        if (clean_line.rfind("instance ", 0) == 0) {
            total_instances++;
            std::string inst_name = trim(clean_line.substr(9));

            std::string description;
            while (std::getline(file, line)) {
                std::string trimmed = trim(line);
                if (!trimmed.empty() && trimmed.find("+++") == std::string::npos) {
                    description = trimmed;
                    break;
                }
            }

            int num_jobs = 0, num_machines = 0;
            file >> num_jobs >> num_machines;

            std::vector<int> proc_times_flat(num_jobs * num_machines, 0);
            for (int j = 0; j < num_jobs; ++j) {
                for (int m = 0; m < num_machines; ++m) {
                    int machine_id = 0, duration = 0;
                    file >> machine_id >> duration;
                    proc_times_flat[j * num_machines + machine_id] = duration;
                }
            }

            int max_iterations = 300;
            std::vector<int> best_seq(num_jobs, 0);
            std::vector<int> history(max_iterations + 1, 0);
            double elapsed_sec = 0.0;

            int best_ms = solve_pfsp("tabu_original", num_jobs, num_machines,
                                     proc_times_flat.data(), max_iterations,
                                     0, // auto tenure
                                     best_seq.data(), history.data(), &elapsed_sec);

            std::cout << "[" << total_instances << "] " << inst_name << " (" << num_jobs << "x"
                      << num_machines << ") | "
                      << "Initial: " << history[0] << " -> Best: " << best_ms
                      << " | Time: " << elapsed_sec << "s\n";
        }
    }

    return 0;
}
