#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#define MAX 99
#define TRUE 1
#define FALSE 0

int N, D, M, type, total = 0;
int UNRESTRICTED = 0, DENSITY = 0, FORBIDDEN = 0;
int a[MAX], p[MAX], b[MAX], f[MAX], fail[MAX];
int d[MAX][MAX], match[MAX][MAX];
FILE *outputFile;
FILE *infoFile;
uint8_t buffer = 0;
int bitCount = 0;
/*------------------------------------------------------------*/
void parse_arguments(int argc, char *argv[]) {
    type = atoi(argv[1]);
    N = atoi(argv[2]);
    if (type == 1) UNRESTRICTED = 1;
    else if (type == 2) DENSITY = 1;
    else if (type == 3) FORBIDDEN = 1;
    if (DENSITY) {
        D = atoi(argv[3]);
    }
    if (FORBIDDEN) {
        M = 0;
        while (argv[3][M] != '\0') {
            f[M + 1] = argv[3][M] - '0';
            M++;
        }
    }
    outputFile = fopen("binaries.bin", "wb");
    infoFile = fopen("info.txt", "w");
    if (outputFile == NULL || infoFile == NULL) {
        printf("error opening files.\n");
        exit(1);
    }
}
/*------------------------------------------------------------*/
void write_bit(int bit) {
    buffer = (buffer << 1) | bit;
    bitCount++;
    if (bitCount == 8) {
        fwrite(&buffer, sizeof(uint8_t), 1, outputFile);
        buffer = 0;
        bitCount = 0;
    }
}
void flush_bits() {
    if (bitCount > 0) {
        buffer <<= (8 - bitCount);
        fwrite(&buffer, sizeof(uint8_t), 1, outputFile);
    }
}
void print() {
    for (int j = 1; j <= N; j++) {
        write_bit(a[j]);
    }
    total++;
}
void print_d(int p) {
    int next = (D / p) * a[p] + a[D % p];
    if (next < N) return;
    int min = 1;
    if ((next == N) && (D % p != 0)) {
        min = b[D % p] + 1;
        p = D;
    }
    else if ((next == N) && (D % p == 0)) min = b[p];
    int end = N;
    for (b[D] = min; b[D] < 2; b[D]++) {
        int i = 1;
        for (int j = 1; j <= end; j++) {
            if (a[i] == j) {
                write_bit(b[i]);
                i++;
            }
            else write_bit(0);
        }
        total++;
        p = D;
    }
}
// subroutines
void set_match(int t) {
    for (int j = t; j < M; j++) {
        if (match[j][t - 1] && f[M - j + t] == a[t]) match[j][t] = TRUE;
        else match[j][t] = FALSE;
    }
}
int check_suffix(int s) {
    while (s > 0) {
        if (match[M - s][M - s] == TRUE) return FALSE;
        else s = fail[s];
    }
    return TRUE;
}
// unrestricted
void gen(int t, int p) {
    if (t > N) {
        if (N % p == 0) print();
    }
    else {
        a[t] = a[t - p];
        gen(t + 1, p);
        for (int j = a[t - p] + 1; j <= 1; j++) {
            a[t] = j;
            gen(t + 1, t);
        }
    }
}
// fixed density
void gen_d(int t, int p) {
    if (t >= D - 1) print_d(p);
    else {
        int tail = N - (D - t) + 1;
        int max = a[t - p + 1] + a[p];
        if (max <= tail) {
            a[t + 1] = max;
            b[t + 1] = b[t - p + 1];
            gen_d(t + 1, p);
            for (int i = b[t + 1] + 1; i < 2; i++) {
                b[t + 1] = i;
                gen_d(t + 1, t + 1);
            }
            tail = max - 1;
        }
        for (int j = tail; j >= a[t] + 1; j--) {
            a[t + 1] = j;
            for (int i = 1; i < 2; i++) {
                b[t + 1] = i;
                gen_d(t + 1, t + 1);
            }
        }
    }
}
// forbidden substrings
void gen_f(int t, int p, int s) {
    if (t > N) {
        if (N % p == 0 && check_suffix(s)) print();
    }
    else {
        a[t] = a[t - p];
        int q = d[s][a[t]];
        if (t < M) set_match(t);
        if (q != M) gen_f(t + 1, p, q);

        for (int j = a[t - p] + 1; j <= 1; j++) {
            a[t] = j;
            q = d[s][j];
            if (t < M) set_match(t);
            if (q != M) gen_f(t + 1, t, q);
        }
    }
}
/*------------------------------------------------------------*/
void init() {
    a[0] = a[1] = 0;
    //----------------
    if (UNRESTRICTED) gen(1, 1);
    //----------------
    if (DENSITY) {
        for (int j = 0; j <= D; j++) a[j] = 0;
        if (D == 0) {
            for (int j = 1; j <= N; j++) write_bit(0);
            total = 1;
        }
        else if (D == 1) {
            for (int i = 1; i < 2; i++) {
                for (int j = 1; j < N; j++) write_bit(0);
                write_bit(i);
            }
            total = 1;
        }
        else {
            a[D] = N;
            for (int j = N - D + 1; j >= (N - 1) / D + 1; j--) {
                a[1] = j;
                for (int i = 1; i < 2; i++) {
                    b[1] = i;
                    gen_d(1, 1);
                }
            }
        }
    }
    //----------------
    if (FORBIDDEN) {
        for (int j = 1; j < M; j++) match[j][0] = TRUE;
        fail[1] = 0;
        for (int j = 2; j <= M; j++) {
            int i = fail[j - 1];
            while (f[j] != f[i + 1] && i > 0) i = fail[i];
            if (f[j] != f[i + 1] && i == 0) fail[j] = 0;
            else fail[j] = i + 1;
        }
        for (int j = 1; j <= M; j++) d[j - 1][f[j]] = j;
        for (int j = 0; j < 2; j++) if (j != f[1]) d[0][j] = 0;
        for (int j = 1; j <= M; j++)
            for (int i = 0; i < 2; i++)
                if (i != f[j + 1]) d[j][i] = d[fail[j]][i];
        gen_f(1, 1, 0);
    }
}
/*------------------------------------------------------------*/
int main(int argc, char *argv[]) {
    parse_arguments(argc, argv);
    init();
    flush_bits();
    fprintf(infoFile, "%d", total);
    fclose(outputFile);
    fclose(infoFile);
    return 0;
}