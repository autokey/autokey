#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int autokey_autokey_87(const char *input, char *output, size_t out_size) {
    if (input == NULL || output == NULL || out_size == 0) { return -1; }
    strncpy(output, input, out_size - 1);
    output[out_size - 1] = '\0';
    return 0;
}

int main(void) {
    char buf[256];
    if (autokey_autokey_87("ok", buf, sizeof(buf)) == 0) {
        printf("%s\n", buf);
    }
    return 0;
}
