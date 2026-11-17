#ifndef FLOWSHOP_ANALYZER_SOLVER_API_H
#define FLOWSHOP_ANALYZER_SOLVER_API_H

#ifdef _WIN32
#define API_EXPORT __declspec(dllexport)
#else
#define API_EXPORT
#endif

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Unified PFSP solver dispatcher.
 *
 * Supported algorithms:
 *   - "tabu_original" : Unoptimized Insertion-neighborhood Tabu Search
 *   - "tabu_optimized": Memory-optimized Insertion-neighborhood Tabu Search
 *   - "tabu_neh"      : NEH-seeded Insertion-neighborhood Tabu Search
 */
API_EXPORT int solve_pfsp(const char *algo_name, int num_jobs, int num_machines,
                          const int *proc_times_flat, int max_iterations, int tabu_tenure,
                          int *out_best_schedule, int *out_history, double *out_elapsed_sec);

#ifdef __cplusplus
}
#endif

#endif // FLOWSHOP_ANALYZER_SOLVER_API_H
