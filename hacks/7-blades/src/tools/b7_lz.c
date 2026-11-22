/* 7 Blades LZ compressor, optimal parse (fewest output bytes).
 * Tokens: b < 0x80: b literal bytes follow; 16-bit BE v >= 0x8000: copy ((~v>>8)&0x7f)+3 bytes from distance (v&0xff)+1.
 * usage: b7_lz in > body   (the caller writes the "1.\." + BE size header) */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int c, char **v)
{
    FILE *f = fopen(v[1], "rb"); fseek(f, 0, 2); long n = ftell(f); fseek(f, 0, 0);
    unsigned char *d = malloc(n + 1); if (fread(d, 1, n, f) != (size_t)n) return 1; fclose(f);
    unsigned char *ml = malloc(n + 1), *md = malloc(n + 1);
    long *cost = malloc((n + 1) * sizeof(long)); int *step = malloc((n + 1) * sizeof(int));
    for (long i = 0; i < n; i++) {          /* longest match at i and its distance */
        int bl = 0, bd = 0;
        for (int D = 1; D <= 256 && D <= i; D++) {
            int L = 0; while (L < 130 && i + L < n && d[i + L - D] == d[i + L]) L++;
            if (L > bl) { bl = L; bd = D; if (L == 130) break; }
        }
        ml[i] = bl; md[i] = bd - 1;   /* distance - 1 fits a byte */
    }
    cost[n] = 0;
    for (long i = n - 1; i >= 0; i--) {     /* step > 0: match length; step < 0: literal run */
        long best = 1L << 60; int bs = 0;
        for (int L = 3; L <= ml[i]; L++) if (2 + cost[i + L] < best) { best = 2 + cost[i + L]; bs = L; }
        for (int k = 1; k <= 127 && i + k <= n; k++) if (k + 1 + cost[i + k] < best) { best = k + 1 + cost[i + k]; bs = -k; }
        cost[i] = best; step[i] = bs;
    }
    unsigned char *o = malloc(cost[0] + 16); long p = 0;
    for (long i = 0; i < n;) {
        int s = step[i];
        if (s > 0) { unsigned w = ((~(s - 3) & 0x7f) << 8) | 0x8000 | md[i]; o[p++] = w >> 8; o[p++] = w & 0xff; i += s; }
        else { o[p++] = -s; memcpy(o + p, d + i, -s); p += -s; i += -s; }
    }
    fwrite(o, 1, p, stdout); return 0;
}
