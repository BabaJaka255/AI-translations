/* 7 Blades (JP, SLPM-65008): English movie subtitles.
 * A port of the PAL subtitle engine (SLES-50109 0x2f3980/0x2f3b28/0x2ef0e0) into the Japanese program.
 * Lives in a new ELF segment; calls Japanese functions by address. Hooks (patched by tools/b7_build_jp.py):
 *   0x385db0 jal play_loop  -> my_play    (movie play function 0x385c20)
 *   0x387b9c jal GetPicture -> my_getpic  (MPEG decode loop 0x387b40)
 *   0x385b10, 0x385b60 jal sceDmaSend -> my_send (vsync movie handler 0x3859e8)
 * eu_font (PAL's English font) replaces kanji1: same rh2 layout and VRAM slot, so the movie subtitles and the
 * in-game text (pal_text, a port of PAL 0x2ee4f8 replacing the JP renderer 0x2f3600) both draw from it.
 */
typedef unsigned long long u64;
typedef unsigned int u32;
typedef unsigned char u8;

#define play_loop   ((void (*)(const char *))0x385e10)
#define get_picture ((int (*)(int *, void *, int))0x3c5738)
#define dma_send    ((void (*)(void *, void *))0x3bd7a0)
#define dma_chan    ((void *(*)(int))0x3bd450)
#define gs_sync     ((int (*)(int, int))0x3bc2c8)
#define flush_cache ((void (*)(int))0x3dc3a0)
#define KANJI1      (*(volatile short *)0x4f11c8)
#define TBP_BASE    (*(volatile int *)0x4f14d8)
#define CBP_BASE    (*(volatile int *)0x4f1514)

struct sub { char key[8]; const u8 *data; };
extern const int sub_count;
extern const struct sub sub_index[];
extern const u8 kern[0xc0];

/* Layout. x is in PAL 512-wide units (as the PAL code computes it), scaled by 5/4 to the 640-wide JP field.
 * y is in JP field lines (224 per field; the 640x320 movie covers lines 32-192). */
#define CW 12           /* glyph width, PAL units */
#define CH 14           /* glyph height, field lines */
#define OX 0x6c00       /* XYOFFSET left edge (0x800-320)<<4 */
#define OY 0x7900       /* top edge (0x800-112)<<4 */
#define SX 20           /* 16 * 5/4 */
#define Y_ONE 200
#define Y_L1  191
#define Y_L2  205

#define NBUF 2         /* the packet is rebuilt only when the text changes */
#define BUFQ 0x1a0      /* quadwords per packet buffer: 6 regs + up to ~80 glyphs*5 + tags */

static u64 pkt[NBUF][BUFQ * 2] __attribute__((aligned(64)));
static void *volatile send_pkt;
static volatile int active;
static int buf;
static const u32 *cur;
static const u8 *base;
static u8 line1[0x80], line2[0x80];
static int x1, x2;
static u64 tex0;
static u64 *q;
static int nad;

static inline void ad(int reg, u64 v) { q[0] = v; q[1] = reg; q += 2; nad++; }

static int text_width(const u8 *s)
{
    int w = 0;
    for (; *s; s++) {
        int c = *s;
        if (c == ' ') w += CW / 2;
        else if (c == '\\') { if (!*++s) break; }
        else if (c >= 0x21 && c < 0x80) w += CW - kern[(c - 0x20) * 2] - kern[(c - 0x20) * 2 + 1] + 8;
    }
    return w;
}

static void draw(const u8 *s, int x, int y)
{
    for (; *s; s++) {
        int c = *s;
        if (c == ' ') { x += CW / 2; continue; }
        if (c < 0x21 || c >= 0x80) continue;
        int i = c - 0x20, row = i >> 4, col = (i & 15) * 16;
        x = x - kern[i * 2] + 4;
        ad(1, 0x80ffffffULL);
        ad(3, (u64)((col + 2) * 16) | (u64)(row << 8) << 16);
        ad(5, (u64)(OX + x * SX) | (u64)(OY + y * 16) << 16);
        ad(3, (u64)((col + 14) * 16) | (u64)((row << 8) | 0xf0) << 16);
        ad(5, (u64)(OX + (x + CW) * SX) | (u64)(OY + (y + CH) * 16) << 16);
        x = x + CW - kern[i * 2 + 1] + 4;
        if (nad > BUFQ - 16) break;
    }
}

static void copy_line(u8 *d, const u8 *s)
{
    int n = 0;
    while (s[n] && s[n] != '\t' && n < 0x7f) { d[n] = s[n]; n++; }
    d[n] = 0;
}

/* The game's texture slots: 0x434180 short handle[36], 0x4341c8 u64 TEX0[36]. Slot 33 is kanji1's fixed slot
 * (eu_font). Read the live TEX0 each frame, as the game's own text draw does, instead of assuming TBP_BASE+0x280,
 * so the subtitles follow the font if the stage loader moves the texture area during a movie. */
#define SLOT_H   ((volatile short *)0x434180)
#define SLOT_T0  ((volatile u64 *)0x4341c8)
static u64 font_tex0(void)
{
    int i, h = KANJI1;
    for (i = 0; i < 36; i++)
        if (SLOT_H[i] == h) {
            u64 t = SLOT_T0[i];
            if ((t & 0x3fff) && ((t >> 20) & 0x3f) == 0x14)   /* PSMT4 */
                return (t & ~(0xfULL << 26 | 0xfULL << 30 | 3ULL << 34 | 0x7ffULL << 51 | 7ULL << 61))
                     | 8ULL << 26 | 8ULL << 30 | 1ULL << 34 | 1ULL << 35 | 2ULL << 51 | 1ULL << 61;
        }
    return (u64)(TBP_BASE + 0x280) | 4ULL << 14 | 0x14ULL << 20 | 8ULL << 26 | 8ULL << 30 | 1ULL << 34 | 1ULL << 35
         | (u64)(CBP_BASE + 0x40) << 37 | 2ULL << 51 | 1ULL << 61;
}

static void build(int frame)
{
    int changed = 0;
    u64 t = font_tex0();
    if (t != tex0) { tex0 = t; changed = line1[0] || line2[0]; }
    if (cur && cur[2] != 0xffffffffu) {
        if ((int)cur[0] <= frame && !line1[0]) {
            changed = 1;
            const u8 *t = base + cur[2];
            copy_line(line1, t);
            x1 = 0x100 - text_width(line1) / 2;
            while (*t && *t != '\t') t++;
            line2[0] = 0;
            if (*t == '\t' && t[1]) {
                copy_line(line2, t + 1);
                x2 = 0x100 - text_width(line2) / 2;
            }
        }
        if ((int)cur[1] <= frame) {
            cur += 3;
            line1[0] = line2[0] = 0;
            changed = 1;
        }
    }
    if (!changed) return;
    if (!line1[0] && !line2[0]) { send_pkt = 0; return; }

    u64 *p = pkt[buf];
    buf = (buf + 1) % NBUF;
    q = p + 4; nad = 0;
    ad(0x3f, 0);                    /* TEXFLUSH */
    ad(0x3b, 0x8000008080ULL);      /* TEXA: AEM, TA0=TA1=0x80 */
    ad(0x14, 0x60);                 /* TEX1: bilinear */
    ad(0x08, 1);                    /* CLAMP_1: clamp (don't rely on the movie's state) */
    ad(0x47, 0x3000d);              /* TEST: alpha > 0, z always */
    ad(0x06, tex0);
    ad(0x00, 0x116);                /* PRIM: sprite, textured, UV */
    if (line2[0]) {
        draw(line1, x1, Y_L1);
        draw(line2, x2, Y_L2);
    } else {
        draw(line1, x1, Y_ONE);
    }
    p[0] = (u64)(nad + 1) | (1ULL << 28);           /* DMA CNT */
    p[1] = 0;
    p[2] = (u64)nad | (1ULL << 15) | (1ULL << 60);  /* GIFtag A+D, EOP */
    p[3] = 0xe;
    q[0] = 7ULL << 28; q[1] = 0;                     /* DMA END */
    flush_cache(0);
    send_pkt = p;
}

static const u8 *find(const char *name)
{
    const char *b = name, *s;
    char key[8];
    int n = 0, i;
    for (s = name; *s; s++)
        if (*s == '/' || *s == '\\' || *s == ':') b = s + 1;
    while (b[n] && b[n] != '_' && b[n] != '.' && b[n] != ';' && n < 7) {
        char c = b[n];
        key[n++] = (c >= 'a' && c <= 'z') ? c - 32 : c;
    }
    key[n] = 0;
    for (i = 0; i < sub_count; i++) {
        const char *k = sub_index[i].key;
        int j = 0;
        while (k[j] && k[j] == key[j]) j++;
        if (!k[j] && !key[j]) return sub_index[i].data;
    }
    return 0;
}

void my_play(const char *name)
{
    const u8 *d = find(name);
    if (d) {
        base = d; cur = (const u32 *)d;
        line1[0] = line2[0] = 0;
        send_pkt = 0;
        tex0 = font_tex0();   /* eu_font, resident in kanji1's slot (my_install) */
        active = 1;
    }
    play_loop(name);
    if (d) {
        active = 0;
        send_pkt = 0;
    }
}

int my_getpic(int *mpeg, void *img, int size)
{
    int r = get_picture(mpeg, img, size);
    if (active) build(mpeg[2]);
    return r;
}

/* Tutorial: fill the JP tutorial's message records (stride 0x15c: id +0x47c, line count +0x480,
 * five 64-byte lines from +0x498) with PAL's English, matched by message id (gen_data.py).
 * Replaces the per-message switch in 0x22fb40; '$/' = next line, '$0'-'$9' = button name string. */
struct tut { int id; const char *text; };
extern const struct tut tut_goku[], tut_yuri[];
#define TUT_BTN ((const u8 *)0x3fbebc)

static void tut_fill(const struct tut *t, int i, u8 *line)
{
    u8 *rec = line - 0x498, *d = line, *end = line + 0x3e;
    const u8 *s = (const u8 *)t[i].text;
    int n = 0;
    *(int *)(rec + 0x47c) = t[i].id;
    while (*s) {
        if (s[0] == '$' && s[1] == '/') {
            *d = 0;
            if (n < 4) n++;
            d = line + n * 0x40; end = d + 0x3e;
            s += 2;
        } else if (s[0] == '$' && s[1] >= '0' && s[1] <= '9') {
            const u8 *b = TUT_BTN + (s[1] - '0') * 0x20;
            while (*b && d < end) *d++ = *b++;
            s += 2;
        } else {
            if (d < end) { d[0] = s[0]; d[1] = s[1]; d += 2; }
            s += 2;
        }
    }
    *d = 0;
    *(int *)(rec + 0x480) = n + 1;
}

void tut_fill_goku(int i, u8 *line) { tut_fill(tut_goku, i, line); }
void tut_fill_yuri(int i, u8 *line) { tut_fill(tut_yuri, i, line); }

/* Tutorial line width for centering (replaces 0x232ea0, which counted 2-byte chars): half the
 * proportional width in pixels at the tutorial's 24-px cell; the caller now multiplies by 1. */
static int text_w16(const u8 *s, int cw);
int tut_width(const u8 *s) { return text_w16(s, 24) >> 5; }

void my_send(void *ch, void *p)
{
    void *s;
    dma_send(ch, p);
    s = send_pkt;
    if (active && s) {
        gs_sync(0, 0);
        dma_send(ch, s);
    }
}

/* ---- In-game text: PAL's English font and proportional renderer ----
 * my_install wraps the kanji1 install (0x2f346c jal): the install buffer then gets eu_font (LZ, same format),
 * so the upload queue puts eu_font into kanji1's VRAM slot. pal_text replaces 0x2f3600 (j at its entry). */
#define tex_install ((int (*)(const char *, u8 *, unsigned, int))0x2f8010)
#define f_7868 ((void (*)(int))0x2f7868)
#define f_7848 ((void (*)(u64))0x2f7848)
#define f_7f78 ((void (*)(int))0x2f7f78)
#define f_6c90 ((void (*)(int))0x2f6c90)
#define f_6ee0 ((void (*)(u64 *))0x2f6ee0)
#define TX_X (*(volatile int *)0x4f04c0)
#define TX_Y (*(volatile int *)0x4f04c4)
#define TX_W (*(volatile int *)0x4f04c8)
#define TX_H (*(volatile int *)0x4f04cc)
#define TX_SAVE (*(int *volatile *)0x4f0550)
#define TX_CUR (*(int *volatile *)0x4f0548)
extern const u8 eufont_lz[], ui_kern[0x200], ui_punct[];
extern const int eufont_lz_size;

int my_install(const char *name, u8 *buf, unsigned size, int flag)
{
    int h = tex_install(name, buf, size, flag), i;
    if ((unsigned)eufont_lz_size <= size)
        for (i = 4; i < eufont_lz_size; i++) buf[i] = eufont_lz[i];   /* keep the 4-byte tag the installer left */
    return h;
}

static int punct(int b)
{
    const u8 *p = ui_punct;
    int i;
    for (i = 0; p[i * 2]; i++)
        if (p[i * 2] == b) return (unsigned)(i - 0x10) <= 3 ? i + 0x8c : i;
    return -1;
}

static int glyph(const u8 *s, int *n)
{
    int c = s[0];
    *n = 2;
    if (c == 0x81) return punct(s[1]);
    if (c == 0x82) {
        int b = s[1];
        if (b >= 0x4f && b < 0x7a) return b - 0x3f;          /* digits, A-Z */
        if (b >= 0x81 && b < 0x9b) return b - 0x40;          /* a-z */
        return -1;
    }
    if (c > 0x20 && c < 0x7f) { *n = 1; return c - 0x20; }
    return -1;
}

/* In-game glyph scale in 1/16 (the project lead 2026-11-10: the JP 24 px kanji cells make the English look ballooned).
 * Glyph width/height and the advance use cw*TXT_SX/16, ch*TXT_SY/16; line pitch and positions stay JP's,
 * and each glyph is centred vertically in its JP line. Variables so test builds can patch them. */
volatile int txt_sx = 16, txt_sy = 16;   /* 2026-11-10 later: PAL's own per-screen sizes instead (b7_build_jp.py) */

/* width in 1/16 px of one line, as pal_text advances */
static int text_w16(const u8 *s, int cw)
{
    cw = cw * txt_sx / 16;
    int w = 0, g, n;
    while (*s && *s != '\n') {
        if (*s == ' ' || (s[0] == 0x81 && s[1] == 0x40)) { w += cw * 8; s += *s == ' ' ? 1 : 2; continue; }
        if (*s == '\t') { s++; continue; }
        if (*s == '\\') { s += 2; continue; }
        g = glyph(s, &n);
        if (g >= 0) w += cw * 16 - (ui_kern[g * 2] + ui_kern[g * 2 + 1]) * cw + txt_sx * 4;
        s += n;
    }
    return w;
}

void pal_text(const u8 *s, int shadow, u64 p3, u64 alpha)
{
    int save = *TX_SAVE;
    u64 a = (alpha & 0xff) << 24, col = a | 0xffffff;
    u64 prim[5] __attribute__((aligned(16)));
    int cw = TX_W * txt_sx / 16, ch0 = TX_H, ch = ch0 * txt_sy / 16, x = TX_X * 16, y = TX_Y * 16 + (ch0 - ch) * 8;
    f_7868(0); f_7848(p3); f_7f78(KANJI1);
    while (*s) {
        int c = *s, g = -1, n = 2;
        if (c == ' ') { x += cw * 8; s++; continue; }
        if (c == '\t') { s++; continue; }
        if (c == '\n') { y += ch0 * 16; x = TX_X * 16; s++; continue; }
        *TX_CUR = KANJI1;
        if (c == '\\') {
            if (s[1] == 'N') col = a | 0xffffff;
            else if (s[1] == 'B') col = a | 0xff0000;
            else if (s[1] == 'R') col = a | 0xff;
        } else if (c == 0x81 && s[1] == 0x40) {
            x += cw * 8; s += 2; continue;
        } else {
            g = glyph(s, &n);
        }
        if (g >= 0) {
            int u = (g & 15) << 8, v = (g >> 4) << 8;
            x -= ui_kern[g * 2] * cw - txt_sx * 2;   /* PAL pads 2 px per side at full size */
            prim[0] = col;
            prim[1] = (u64)(u + 8) | (u64)(v + 8) << 16;
            prim[2] = (u64)(u + 0xf8) | (u64)(v + 0xf8) << 16;
            prim[3] = (u64)(x + 0x6c00) | (u64)(y + 0x7200) << 16;
            prim[4] = (u64)(x + cw * 16 + 0x6c00) | (u64)(y + ch * 16 + 0x7200) << 16;
            f_6c90(0x4011);
            f_6ee0(prim);
            if (shadow) {
                f_6c90(0x4010);
                prim[0] = a | 0x10101;
                prim[3] += 0x20 | 0x20ULL << 16;   /* PAL: 2 px */
                prim[4] += 0x20 | 0x20ULL << 16;
                f_6ee0(prim);
                prim[0] = col;
            }
            x += cw * 16 - (ui_kern[g * 2 + 1] * cw - txt_sx * 2);
        }
        s += n;
    }
    *TX_SAVE = save;
}

/* ---- Status popups (Stun, Power up, ...): PAL's English caption under the kanji frame ----
 * PAL loads <name>_e.rh2 next to each status texture (0x2dfbb8...) and its frame draw (0x2df4b0, JP 0x2e7678)
 * narrows the 64x32 frame to 96 px and adds the 128x16 caption, 16 lines high, right under it.
 * my_status_load wraps the 11 JP loads (0x2e7c0c...) and remembers the caption handle per JP handle;
 * my_status_draw replaces 0x2e7678 (j at its entry). The _e images are added to effect.r by b7_peace.py. */
#define tex_load ((int (*)(const char *))0x2f81f8)
#define ST_N 16
static short st_jp[ST_N], st_en[ST_N];
static const char *st_name[ST_N];

int my_status_load(const char *name)
{
    char buf[48];
    int h = tex_load(name), i, n = 0, k;
    for (i = 0; name[i] && name[i] != '.' && n < 36; i++) buf[n++] = name[i];
    if (n >= 4 && buf[n - 4] == '/' && buf[n - 3] == 'k' && buf[n - 2] == 'o' && buf[n - 1] == 'n') buf[n - 3] = 'c';   /* PAL: con_e */
    buf[n++] = '_'; buf[n++] = 'e'; buf[n++] = '.'; buf[n++] = 'r'; buf[n++] = 'h'; buf[n++] = '2'; buf[n] = 0;
    for (k = 0; k < ST_N && st_name[k] && st_name[k] != name; k++) ;
    if (k < ST_N) { st_name[k] = name; st_jp[k] = h; st_en[k] = tex_load(buf); }
    return h;
}

void my_status_draw(int idx, short *st, int count, int alpha)
{
    char *e = (char *)(0x5fa340 + idx * 0x90);
    u64 prim[5] __attribute__((aligned(16)));
    int t, y, en = -1, k;
    if (!*(volatile short *)(e + 8)) return;
    t = *(volatile int *)(e + 0xc);
    if (alpha <= 0) return;
    f_6c90(0x3fff); f_7848(1); f_7868(0);
    f_7f78(st[1 + (t / 2) % count]);
    y = *(volatile short *)0x4f0480;
    prim[0] = ((u64)alpha << 24) | 0x808080;
    prim[1] = 0;
    prim[2] = 0x02000400;
    prim[3] = 0x00ffffff00007d00ULL | ((u64)(y + 0x894) << 20);
    prim[4] = 0x00ffffff00008300ULL | ((u64)(y + 0x8d4) << 20);
    f_6ee0(prim);
    for (k = 0; k < ST_N && st_name[k]; k++)
        if (st_jp[k] == st[0]) en = st_en[k];
    if (en < 0) return;
    f_7f78(en);
    prim[2] = 0x800 | (0x10ULL << 20);
    prim[3] = 0x00ffffff00007d00ULL | ((u64)(y + 0x8d4) << 20);
    prim[4] = 0x00ffffff00008300ULL | ((u64)(y + 0x8e4) << 20);
    f_6ee0(prim);
}

/* Save screen: PAL's English sprite rectangles (savefix.h, from tools/b7_savefix.py) and the extra
   sprites PAL draws in some states. my_save_fix runs as the tail of the JP setup routine 0x35f860
   (its jr ra becomes j my_save_fix); my_save_draw replaces the message draw call at 0x3621b0. */
#include "savefix.h"
#define SAVE_SPR(k) ((char *)0x46da48 + (k) * 0x2c)
#define save_draw ((void (*)(int, int))0x363fc0)
#define SAVE_STATE (*(volatile short *)0x46f33c)
#define SAVE_OVERWRITE (*(volatile short *)0x46f34a)
void my_save_fix(void)
{
    unsigned i;
    for (i = 0; i < sizeof save_fix / sizeof save_fix[0]; i++)
        *(short *)(SAVE_SPR(save_fix[i][0]) + save_fix[i][1]) = save_fix[i][2];
    for (i = 0; i < sizeof save_fix_handle / sizeof save_fix_handle[0]; i++)
        *(int *)(SAVE_SPR(save_fix_handle[i][0]) + 0xc) = *(int *)save_fix_handle[i][1];
}
void my_save_draw(int first, int last)
{
    int s = SAVE_STATE;
    save_draw(first, last);
    /* PAL: "SAVE FAILED." header over the card error messages; second lines of split messages */
    if (s == 0x3f0) save_draw(59, 59);                 /* "...with at least 335KB" + "of free space ..." */
    if (s == 0x3f1) save_draw(60, 60);
    if (s == 0x3f0 || s == 0x3f1 || s == 0x3f5 || s == 0x1c5 || (first == 0x14 && last == 0x19)) save_draw(29, 29);
    if (s == 0x3f8 && SAVE_OVERWRITE == 1) save_draw(50, 50);   /* autosave note: "at the last save location," */
}

/* Load screen: same for its sprite table (setup 0x35bf80, tail j my_load_fix; draw call at 0x35d0fc).
   PAL heads the card error messages with "Data read failure!" (sprite 4). */
#define LOAD_SPR(k) ((char *)0x46a030 + (k) * 0x2c)
#define load_draw ((void (*)(int, int))0x35f378)
void my_load_fix(void)
{
    unsigned i;
    for (i = 0; i < sizeof load_fix / sizeof load_fix[0]; i++)
        *(short *)(LOAD_SPR(load_fix[i][0]) + load_fix[i][1]) = load_fix[i][2];
    for (i = 0; i < sizeof load_fix_handle / sizeof load_fix_handle[0]; i++)
        if (load_fix_handle[i][0] >= 0)
            *(int *)(LOAD_SPR(load_fix_handle[i][0]) + 0xc) = *(int *)load_fix_handle[i][1];
}
void my_load_draw(int first, int last)
{
    load_draw(first, last);
    if ((first == 8 && last == 11) || (first == 12 && last == 13) || (first == 13 && last == 13) ||
        (first == 17 && last == 18) || (first == 16 && last == 16) || (first == 5 && last == 7))
        load_draw(4, 4);
}

/* Item screen command labels (0x37911c): PAL splits the pouch label into "Quick" and "Item" below it. */
#define set_size ((void (*)(int, int))0x2f3550)
#define set_pos  ((void (*)(int, int))0x2f3560)
#define draw_35e0 ((void (*)(const u8 *))0x2f35e0)
#define draw_35f0 ((void (*)(const u8 *))0x2f35f0)
static const u8 item_label[] = { 0x82, 0x68, 0x82, 0x94, 0x82, 0x85, 0x82, 0x8d, 0 };   /* Ｉｔｅｍ (PAL 0x50e630) */
void my_cmd_label(const u8 *s)
{
    draw_35f0(s);
    if (s == *(const u8 *const *)0x4750bc) {
        set_size(16, 16);
        set_pos(0xe0 + 0x20, 0x186);
        draw_35e0(item_label);
        draw_35f0(item_label);
    }
}

/* Options screens (title 0x368e08.., in-game 0x37bd10..): PAL's English labels in the JP layout.
   The option sprites live in one table (80 records of 0x2c at 0x478f3c, plus 88-90 for the in-game "Return to title?" dialog); every option draw goes
   through the sprite builder 0x37b538, here via my_optspr, which draws a translated copy of the
   record: the JP sheet + source rectangle is looked up in opt_map (optfix.h, tools/b7_optfix.py)
   and replaced by PAL's image on one of PAL's three sheets FONT1-3_u, moved by opt_dx[slot], with
   the width of the English image. The JP code and its records are left as they are. FONT1/Font2
   now hold PAL's FONT1_u/FONT2_u (b7_peace.py); FONT3 is loaded next to them by my_optload*. */
#include "optfix.h"
#define OPT_REC 0x478f3c
#define OPT_H0 (*(volatile int *)0x47a3f8)
#define OPT_H1 (*(volatile int *)0x47a3fc)
#define opt_build ((void (*)(void *, void *, int, int))0x37b538)
#define tex_load ((int (*)(const char *))0x2f81f8)
volatile int opt_h3;
int my_optload_title(const char *font2)
{
    int h = tex_load(font2);
    opt_h3 = tex_load("taku_save/load_data/FONT3.rh2");
    return h;
}
int my_optload_game(const char *font2)
{
    int h = tex_load(font2);
    opt_h3 = tex_load("taku_data/FONT3.rh2");
    return h;
}
static const short *opt_find(unsigned k, int s, const short *uv)
{
    unsigned i;
    for (i = 0; i < sizeof opt_slot / sizeof opt_slot[0]; i++)
        if (opt_slot[i][0] == (short)k && opt_slot[i][1] == s && opt_slot[i][2] == uv[0] && opt_slot[i][3] == uv[1] &&
            opt_slot[i][4] == uv[2] && opt_slot[i][5] == uv[3]) return opt_slot[i] + 1;
    for (i = 0; i < sizeof opt_map / sizeof opt_map[0]; i++)
        if (opt_map[i][0] == s && opt_map[i][1] == uv[0] && opt_map[i][2] == uv[1] && opt_map[i][3] == uv[2] &&
            opt_map[i][4] == uv[3]) return opt_map[i];
    return 0;
}
void my_optspr(void *pkt, void *rec, int x, int y)
{
    unsigned k = ((u32)rec - OPT_REC) / 0x2c;
    u32 r[11];
    short *uv = (short *)(r + 6);
    const short *m;
    int h, s, i;
    if ((u32)rec < OPT_REC || k >= sizeof opt_dx) { opt_build(pkt, rec, x, y); return; }
    for (i = 0; i < 11; i++) r[i] = ((u32 *)rec)[i];
    h = r[3]; s = h == OPT_H0 ? 0 : h == OPT_H1 ? 1 : -1;
    m = s < 0 ? 0 : opt_find(k, s, uv);
    if (m) {
        if (m[5] < 0) { uv[2] = uv[0]; uv[6] = uv[4]; }           /* hidden: zero-width sprite */
        else {
            r[3] = m[5] == 0 ? OPT_H0 : m[5] == 1 ? OPT_H1 : opt_h3;
            uv[0] = m[6]; uv[1] = m[7]; uv[2] = m[8]; uv[3] = m[9];
            uv[4] += opt_dx[k]; uv[6] = uv[4] + (m[8] - m[6]);
        }
    }
    opt_build(pkt, r, x, y);
}

/* Cursor bars of the options screens (shorts after the 91 sprite records, 0x479ee0): PAL's extents for
   the wider English labels (PAL setups 0x36da50 / 0x381780). Runs as the tail of the JP setups. */
#define OPT_BAR ((volatile short *)0x479ee0)
static void opt_bar(int rows)
{
    int i;
    for (i = 0; i < rows - 1; i++) OPT_BAR[30 + i] = 496;     /* menu rows: right edge (JP 266..450) */
    OPT_BAR[30 + rows - 1] = rows == 7 ? 424 : 408;           /* Return to title */
    OPT_BAR[46] = 496;                                         /* current bar (row 0) */
    OPT_BAR[62] = OPT_BAR[63] = 256; OPT_BAR[84] = OPT_BAR[85] = 384;   /* volume screen: Return */
    for (i = 104; i < 110; i++) OPT_BAR[i] = 72;               /* control screen: left column */
}
void my_optfix_game(void) { opt_bar(7); }
void my_optfix_title(void) { opt_bar(6); }
