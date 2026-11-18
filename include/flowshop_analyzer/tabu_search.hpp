#ifndef FLOWSHOP_ANALYZER_TABU_SEARCH_HPP
#define FLOWSHOP_ANALYZER_TABU_SEARCH_HPP

#include <vector>

std::vector<int> tabuSearchPFSP(int num_jobs, int num_machines,
                                const std::vector<std::vector<int>> &proc_times, int max_iterations,
                                int tabu_tenure, int &final_makespan,
                                std::vector<int> *convergence_history = nullptr);

std::vector<int> tabuSearchOptimizedPFSP(int num_jobs, int num_machines,
                                         const std::vector<std::vector<int>> &proc_times,
                                         int max_iterations, int tabu_tenure, int &final_makespan,
                                         std::vector<int> *convergence_history = nullptr);

std::vector<int> tabuSearchNEHPFSP(int num_jobs, int num_machines,
                                   const std::vector<std::vector<int>> &proc_times,
                                   int max_iterations, int tabu_tenure, int &final_makespan,
                                   std::vector<int> *convergence_history = nullptr);

#endif // FLOWSHOP_ANALYZER_TABU_SEARCH_HPP
