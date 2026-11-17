#include "flowshop_analyzer/tabu_search.hpp"

#include <algorithm>
#include <limits>
#include <numeric>
#include <vector>

static int calculateMakespan(const int *perm, int n, int num_machines,
                             const std::vector<std::vector<int>> &proc_times,
                             int *completion_times) {
    if (n == 0)
        return 0;

    for (int m = 0; m < num_machines; ++m) {
        completion_times[m] = 0;
    }

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

static void applyInsertMove(const int *src, int n, int from, int to, int *dst) {
    int moved_job = src[from];
    if (from < to) {
        std::copy(src, src + from, dst);
        std::copy(src + from + 1, src + to + 1, dst + from);
        dst[to] = moved_job;
        std::copy(src + to + 1, src + n, dst + to + 1);
    } else {
        std::copy(src, src + to, dst);
        dst[to] = moved_job;
        std::copy(src + to, src + from, dst + to + 1);
        std::copy(src + from + 1, src + n, dst + from + 1);
    }
}

static std::vector<int> generateNEHInitialSolution(int num_jobs, int num_machines,
                                                   const std::vector<std::vector<int>> &proc_times,
                                                   int *completion_times) {
    if (num_jobs <= 0)
        return {};
    if (num_jobs == 1)
        return {0};

    std::vector<int> total_proc(num_jobs, 0);
    for (int j = 0; j < num_jobs; ++j) {
        for (int m = 0; m < num_machines; ++m) {
            total_proc[j] += proc_times[j][m];
        }
    }

    std::vector<int> sorted_jobs(num_jobs);
    std::iota(sorted_jobs.begin(), sorted_jobs.end(), 0);
    std::stable_sort(sorted_jobs.begin(), sorted_jobs.end(),
                     [&](int a, int b) { return total_proc[a] > total_proc[b]; });

    std::vector<int> partial_seq;
    partial_seq.reserve(num_jobs);

    int j0 = sorted_jobs[0];
    int j1 = sorted_jobs[1];

    int seq_a[2] = {j0, j1};
    int seq_b[2] = {j1, j0};
    int ms_a = calculateMakespan(seq_a, 2, num_machines, proc_times, completion_times);
    int ms_b = calculateMakespan(seq_b, 2, num_machines, proc_times, completion_times);

    if (ms_a <= ms_b) {
        partial_seq.push_back(j0);
        partial_seq.push_back(j1);
    } else {
        partial_seq.push_back(j1);
        partial_seq.push_back(j0);
    }

    std::vector<int> candidate(num_jobs);
    for (int k = 2; k < num_jobs; ++k) {
        int job = sorted_jobs[k];
        int best_pos = -1;
        int best_ms = std::numeric_limits<int>::max();

        for (int pos = 0; pos <= k; ++pos) {
            std::copy(partial_seq.begin(), partial_seq.begin() + pos, candidate.begin());
            candidate[pos] = job;
            std::copy(partial_seq.begin() + pos, partial_seq.begin() + k,
                      candidate.begin() + pos + 1);

            int ms = calculateMakespan(candidate.data(), k + 1, num_machines, proc_times,
                                       completion_times);
            if (ms < best_ms) {
                best_ms = ms;
                best_pos = pos;
            }
        }

        partial_seq.insert(partial_seq.begin() + best_pos, job);
    }

    return partial_seq;
}

std::vector<int> tabuSearchNEHPFSP(int num_jobs, int num_machines,
                                   const std::vector<std::vector<int>> &proc_times,
                                   int max_iterations, int tabu_tenure, int &final_makespan,
                                   std::vector<int> *convergence_history) {
    if (num_jobs <= 0 || num_machines <= 0) {
        final_makespan = 0;
        return {};
    }

    int effective_tenure = (tabu_tenure > 0) ? tabu_tenure : std::max(5, num_jobs * 10 / 11);

    std::vector<int> completion_times(num_machines, 0);
    std::vector<int> current_sol =
        generateNEHInitialSolution(num_jobs, num_machines, proc_times, completion_times.data());

    int current_ms = calculateMakespan(current_sol.data(), num_jobs, num_machines, proc_times,
                                       completion_times.data());

    std::vector<int> best_sol = current_sol;
    int best_ms = current_ms;

    if (convergence_history != nullptr) {
        convergence_history->clear();
        convergence_history->reserve(max_iterations + 1);
        convergence_history->push_back(best_ms);
    }

    std::vector<int> tabu_list(num_jobs * num_jobs, 0);
    std::vector<int> neighbor_sol(num_jobs);

    for (int iter = 1; iter <= max_iterations; ++iter) {
        int best_neighbor_ms = std::numeric_limits<int>::max();
        int best_from = -1;
        int best_to = -1;
        int best_moved_job = -1;

        for (int i = 0; i < num_jobs; ++i) {
            int moved_job = current_sol[i];
            for (int j = 0; j < num_jobs; ++j) {
                if (i == j)
                    continue;

                applyInsertMove(current_sol.data(), num_jobs, i, j, neighbor_sol.data());

                int neighbor_ms = calculateMakespan(neighbor_sol.data(), num_jobs, num_machines,
                                                    proc_times, completion_times.data());
                bool is_tabu = (tabu_list[moved_job * num_jobs + j] >= iter);
                bool aspiration = (neighbor_ms < best_ms);

                if ((!is_tabu || aspiration) && neighbor_ms < best_neighbor_ms) {
                    best_neighbor_ms = neighbor_ms;
                    best_from = i;
                    best_to = j;
                    best_moved_job = moved_job;
                }
            }
        }

        if (best_moved_job == -1)
            break;

        applyInsertMove(current_sol.data(), num_jobs, best_from, best_to, neighbor_sol.data());
        std::copy(neighbor_sol.begin(), neighbor_sol.end(), current_sol.begin());
        current_ms = best_neighbor_ms;
        tabu_list[best_moved_job * num_jobs + best_from] = iter + effective_tenure;

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
