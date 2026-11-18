#include "flowshop_analyzer/solver_api.h"
#include "flowshop_analyzer/tabu_search.hpp"

#include <algorithm>
#include <chrono>
#include <string>
#include <unordered_map>
#include <vector>

using SolverAdapter = std::vector<int> (*)(int, int, const std::vector<std::vector<int>> &, int,
                                           int, int &, std::vector<int> *);

extern "C" int solve_pfsp(const char *algo_name, int num_jobs, int num_machines,
                          const int *proc_times_flat, int max_iterations, int tabu_tenure,
                          int *out_best_schedule, int *out_history, double *out_elapsed_sec) {
    if (algo_name == nullptr || proc_times_flat == nullptr || num_jobs <= 0 || num_machines <= 0 ||
        max_iterations < 1) {
        return -1;
    }

    static const std::unordered_map<std::string, SolverAdapter> registry = {
        {"tabu_original", &tabuSearchPFSP},
        {"tabu_optimized", &tabuSearchOptimizedPFSP},
        {"tabu_neh", &tabuSearchNEHPFSP},
    };

    auto it = registry.find(algo_name);
    if (it == registry.end()) {
        return -1;
    }

    std::vector<std::vector<int>> proc_times(num_jobs, std::vector<int>(num_machines, 0));
    for (int j = 0; j < num_jobs; ++j) {
        for (int m = 0; m < num_machines; ++m) {
            proc_times[j][m] = proc_times_flat[j * num_machines + m];
        }
    }

    int final_makespan = 0;
    std::vector<int> history;

    auto start = std::chrono::high_resolution_clock::now();
    std::vector<int> best_seq = it->second(num_jobs, num_machines, proc_times, max_iterations,
                                           tabu_tenure, final_makespan, &history);
    auto end = std::chrono::high_resolution_clock::now();

    if (out_elapsed_sec != nullptr) {
        std::chrono::duration<double> elapsed = end - start;
        *out_elapsed_sec = elapsed.count();
    }

    if (out_best_schedule != nullptr) {
        std::copy(best_seq.begin(), best_seq.end(), out_best_schedule);
    }

    if (out_history != nullptr) {
        std::copy(history.begin(), history.end(), out_history);
    }

    return final_makespan;
}
