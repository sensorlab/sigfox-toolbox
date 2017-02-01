#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#include <libopencm3/stm32/usart.h>

#include "manuf_api.h"
#include "sigfox_api.h"

const sfx_u8 sigfox_key[16] = {
	0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

/* note: id is sent in little-endian order */
const sfx_u8 id[4]  = {0x00, 0x00, 0x00, 0x00};

sfx_std_t standard = SFX_STD_ETSI;
sfx_u32 TxFrequency = 868130000;
sfx_u32 RxFrequency = 869525000;

#define USART_BUFFER_SIZE		128

static char usart_buffer[USART_BUFFER_SIZE];
static int usart_buffer_len = 0;
static volatile int usart_buffer_attn = 0;

static void hex_to_u8(const char* hex, sfx_u8* bin, unsigned* len)
{
	sfx_u8 *dst = bin;
	const char *src = hex;
	unsigned u;

	*len = 0;
	while (sscanf(src, "%2x", &u) == 1) {
		*dst = u;
		dst++;

		src += 2;
		*len += 1;
	}
}

static void command_send_frame(const char* frame)
{
	sfx_u8 data[12];
	unsigned len;

	hex_to_u8(frame, data, &len);
	SIGFOX_API_send_frame(data, len, NULL, 2,  SFX_FALSE);
	printf("ok\n");
}

static char* trim(char* cmd)
{
	char* end = cmd + strlen(cmd) - 1;
	while(end > cmd && isspace((int) *end)) end--;
	end++;

	*end = 0;

	return cmd;
}

static void dispatch(char* cmdi)
{
	int datatype, value;
	char hex[32];

	char* cmd = trim(cmdi);

	if (sscanf(cmd, "set_nv_mem %d %d", &datatype, &value) == 2) {
		MANUF_API_set_nv_mem(datatype, value);
		printf("ok\n");
	} else if (!strcmp(cmd, "sigfox_api_open")) {
		SIGFOX_API_open(TxFrequency,    /* TX Frequency */
				RxFrequency,    /* RX Frequency */
				(sfx_u8*)&id,   /* Pointer on the Id */
				standard);      /* Standard */
		printf("ok\n");
	} else if (!strcmp(cmd, "sigfox_api_close")) {
		SIGFOX_API_close();
		printf("ok\n");
	} else if (sscanf(cmd, "send_frame %24s", hex) == 1) {
		command_send_frame(hex);
	} else {
		printf("error: unknown command: %s\n", cmd);
	}
}

void usart1_isr(void)
{
	/* Check if we were called because of RXNE. */
	if (((USART_CR1(USART1) & USART_CR1_RXNEIE) != 0) &&
	    ((USART_SR(USART1) & USART_SR_RXNE) != 0)) {

		char c = usart_recv(USART1);

		/* If we haven't yet processed previous command ignore input */
		if (!usart_buffer_attn) {
			if (c == '\n' || c == 0 || usart_buffer_len >= (USART_BUFFER_SIZE-1)) {
				usart_buffer[usart_buffer_len] = 0;
				usart_buffer_len = 0;
				usart_buffer_attn = 1;
			} else {
				usart_buffer[usart_buffer_len] = c;
				usart_buffer_len++;
			}
		}
	}
}

void demo_main(void)
{
	while(1) {
		if (usart_buffer_attn) {
			dispatch(usart_buffer);
			usart_buffer_attn = 0;
		}
	}
}
