#include <stdio.h>
#include <errno.h>
#include <libopencm3/stm32/f1/rcc.h>
#include <libopencm3/stm32/f1/gpio.h>
#include <libopencm3/stm32/f1/scb.h>
#include <libopencm3/stm32/nvic.h>
#include <libopencm3/stm32/usart.h>

#include "sigfox.h"

extern void (*const vector_table[]) (void);

/* Set up all the peripherals */

static void setup_usart(void)
{
	/* GPIO pin for USART TX */
	gpio_set_mode(GPIOA, GPIO_MODE_OUTPUT_50_MHZ,
			GPIO_CNF_OUTPUT_ALTFN_PUSHPULL, GPIO9);

	/* GPIO pin for USART RX */
	gpio_set_mode(GPIOA, GPIO_MODE_INPUT,
		      GPIO_CNF_INPUT_FLOAT, GPIO10);

	/* Setup USART parameters. */
	usart_set_baudrate(USART1, 115200);
	usart_set_databits(USART1, 8);
	usart_set_stopbits(USART1, USART_STOPBITS_1);
	usart_set_parity(USART1, USART_PARITY_NONE);
	usart_set_flow_control(USART1, USART_FLOWCONTROL_NONE);
	usart_set_mode(USART1, USART_MODE_TX_RX);

	/* Enable usart Receive interrupt. */
	USART_CR1(USART1) |= USART_CR1_RXNEIE;

	/* Finally enable the USART. */
	usart_enable(USART1);
}

static void setup(void)
{
	SCB_VTOR = (u32) vector_table;
	asm volatile ("cpsie i");

	rcc_peripheral_enable_clock(&RCC_APB2ENR,
			RCC_APB2ENR_IOPAEN |
			RCC_APB2ENR_IOPBEN |
			RCC_APB2ENR_AFIOEN |
			RCC_APB2ENR_USART1EN);

	nvic_enable_irq(NVIC_USART1_IRQ);
	nvic_set_priority(NVIC_USART1_IRQ, 0);

	setup_usart();
}

/* Provide _write syscall used by libc */
int _write(int file, char *ptr, int len)
{
	int i;

	if (file == 1) {
		for (i = 0; i < len; i++) {
			usart_send_blocking(USART1, ptr[i]);
		}
		return i;
	} else {
		errno = EIO;
		return -1;
	}
}

/* Delay execution for some arbitrary amount of time */
void delay(void)
{
	int i;

	for (i = 0; i < 8000000; i++) {
		__asm__("nop");
	}
}

int main(void)
{
	setup();

	printf("boot\n");

	while (1) {
		gpio_toggle(GPIOB, GPIO2);
		printf("run demo\n");
		demo_main();
		//delay();
	}

	return 0;
}
