double ce_getcost(double *in_array, int size, double threshold, char costfn, int step);
double ce_thresnode(double *in_array, double *out_array, int size, double threshold, char type);
double ce_thresnode2(double *in_array, int size, double threshold, char type);
void ce_energycurve(double *arrE, double *arrC, int N, int M);
void ce_sumsquares(double *arr, int W, double *out);
