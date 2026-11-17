#include "flowshop_analyzer/tabu_search.hpp"

#include <algorithm>
#include <limits>
#include <numeric>
#include <vector>

static int calculateMakespan(const std::vector<int> &perm, int num_machines,
                             const std::vector<std::vector<int>> &proc_times) {
    int n = static_cast<int>(perm.size());
    if (n == 0)
        return 0;

    std::vector<int> completion_times(num_machines, 0);
    for (int i = 0; i < n; ++i) {
        int job = perm[i];
        completion_times[0] += proc_times[job][0];
        for (int m = 1; m < num_machines; ++m) {
            completion_times[m] =
                std::max(completion_times[m], completion_times[m - 1]) + proc_times[job][m];
        }
    }
    return completion_times[num_machines - 1];
}

static std::vector<int> generateInitialSolution(int num_jobs) {
    std::vector<int> initial_seq(num_jobs);
    std::iota(initial_seq.begin(), initial_seq.end(), 0);
    return initial_seq;
}

std::vector<int> tabuSearchPFSP(int num_jobs, int num_machines,
                                const std::vector<std::vector<int>> &proc_times, int max_iterations,
                                int tabu_tenure, int &final_makespan,
                                std::vector<int> *convergence_history) {
    int effective_tenure = (tabu_tenure > 0) ? tabu_tenure : std::max(5, num_jobs * 10 / 11);

    std::vector<int> current_sol = generateInitialSolution(num_jobs);
    int current_ms = calculateMakespan(current_sol, num_machines, proc_times);
    std::vector<int> best_sol = current_sol;
    int best_ms = current_ms;

    if (convergence_history != nullptr) {
        convergence_history->clear();
        convergence_history->reserve(max_iterations + 1);
        convergence_history->push_back(best_ms);
    }

    std::vector<std::vector<int>> tabu_list(num_jobs, std::vector<int>(num_jobs, 0));

    for (int iter = 1; iter <= max_iterations; ++iter) {
        int best_neighbor_ms = std::numeric_limits<int>::max();
        int best_from = -1;
        int best_moved_job = -1;
        std::vector<int> best_neighbor_sol;

        for (int i = 0; i < num_jobs; ++i) {
            for (int j = 0; j < num_jobs; ++j) {
                if (i == j)
                    continue;

                std::vector<int> neighbor = current_sol;
                int moved_job = neighbor[i];
                neighbor.erase(neighbor.begin() + i);
                neighbor.insert(neighbor.begin() + j, moved_job);

                int neighbor_ms = calculateMakespan(neighbor, num_machines, proc_times);
                bool is_tabu = (tabu_list[moved_job][j] >= iter);
                bool aspiration = (neighbor_ms < best_ms);

                if ((!is_tabu || aspiration) && neighbor_ms < best_neighbor_ms) {
                    best_neighbor_ms = neighbor_ms;
                    best_from = i;
                    best_moved_job = moved_job;
                    best_neighbor_sol = neighbor;
                }
            }
        }

        if (best_moved_job == -1)
            break;

        current_sol = best_neighbor_sol;
        current_ms = best_neighbor_ms;
        tabu_list[best_moved_job][best_from] = iter + effective_tenure;

        if (current_ms < best_ms) {
            best_ms = current_ms;
            best_sol = current_sol;
        }

        if (convergence_history != nullptr) {
            convergence_history->push_back(best_ms);
        }
    }

    if (convergence_history != nullptr) {
        while (static_cast<int>(convergence_history->size()) <= max_iterations) {
            convergence_history->push_back(best_ms);
        }
    }

    final_makespan = best_ms;
    return best_sol;
}
