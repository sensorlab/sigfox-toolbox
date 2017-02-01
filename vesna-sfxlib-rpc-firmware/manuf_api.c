#include <stdio.h>
#include <stdlib.h>

#include "sigfox.h"
#include "aes_128.h"
#include "manuf_api.h"

// "debugging"

static void sfx_u8_dump(sfx_u8 *data, sfx_u8 len)
{
	int n;
	printf("  [ ");
	for(n = 0; n < len; n++) {
		printf("%02x ", data[n]);
	}
	printf("]\n");
}

// stub functions

// this should be non-volatile
#define nv_mem_size 3
static sfx_u16 nv_mem[nv_mem_size];

sfx_error_t MANUF_API_malloc(sfx_u16 size, sfx_u8 **returned_pointer)
{
	printf("# malloc(%d, %p)\n", size, returned_pointer);
	void *p = malloc(size);

	if(p != NULL) {
		*returned_pointer = (sfx_u8*) p;
		return SFX_ERR_MANUF_NONE;
	} else {
		return SFX_ERR_MANUF_MALLOC;
	}
}

sfx_error_t MANUF_API_free(sfx_u8 *p)
{
	printf("# free(%p)\n", p);

	free(p);

	return SFX_ERR_MANUF_NONE;
}

sfx_error_t MANUF_API_get_voltage_temperature(sfx_u16 *voltage_idle,
                                              sfx_u16 *voltage_tx,
                                              sfx_u16 *temperature)
{
	printf("# get_voltage_temperature(%p, %p, %p)\n",
			voltage_idle, voltage_tx, temperature);

	return SFX_ERR_MANUF_NONE;
}

sfx_error_t MANUF_API_rf_init(sfx_rf_mode_t rf_mode)
{
	printf("# rf_init(%d)\n", rf_mode);

	return SFX_ERR_MANUF_NONE;
}

sfx_error_t MANUF_API_rf_stop(void)
{
	printf("# rf_stop()\n");
	return SFX_ERR_MANUF_NONE;
}

sfx_error_t MANUF_API_rf_send(sfx_u8 *stream,
                              sfx_u8 size)
{
	printf("# rf_send(%p, %d)\n#", stream, size);
	sfx_u8_dump(stream, size);

	printf("rf_send ");
	unsigned n;
	for(n = 0; n < size; n++) {
		printf("%02x", stream[n]);
	}
	printf("\n");

	return SFX_ERR_MANUF_NONE;
}

sfx_error_t MANUF_API_delay(sfx_delay_t delay_type)
{
	printf("# delay(%d)\n", delay_type);
	printf("delay %d\n", delay_type);
	return SFX_ERR_MANUF_NONE;
}

sfx_error_t MANUF_API_change_frequency(sfx_u32 frequency)
{
	printf("# change_frequency(%lu)\n", frequency);
	printf("change_frequency %lu\n", frequency);
	return SFX_ERR_MANUF_NONE;
}

sfx_error_t MANUF_API_aes_128_cbc_encrypt(sfx_u8 *encrypted_data,
                                          sfx_u8 *data_to_encrypt,
                                          sfx_u8 data_len)
{
	printf("# aes128_cbc_encrypt(%p, %p, %d)\n#<", encrypted_data,
			data_to_encrypt, data_len);

	sfx_u8_dump(data_to_encrypt, data_len);

	/* copied from sigfox example */
	sfx_u8 i, j, blocks;
	sfx_u8 cbc[16] = {0x00};

	blocks = data_len / 16;
	for(i = 0; i < blocks; i++)
	{
		for(j = 0; j < 16; j++)
		{
			cbc[j] ^= data_to_encrypt[j+i*16];
		}

		aes_enc_dec(cbc, sigfox_key, 0);

		for(j = 0; j < 16; j++)
		{
			encrypted_data[j+(i*16)] = cbc[j];
			//encrypted_data[j+(i*16)] = 0;
			//encrypted_data[j+(i*16)] = data_to_encrypt[j+i*16];
		}
	}

	printf("#>");
	sfx_u8_dump(encrypted_data, data_len);

	return SFX_ERR_MANUF_NONE;
}

sfx_error_t MANUF_API_get_nv_mem(sfx_nvmem_t nvmem_datatype,
				 sfx_u16 *return_value)
{
	printf("# get_nv_mem(%d, %p)\n", nvmem_datatype, return_value);

	if(nvmem_datatype >= nv_mem_size) {
		return SFX_ERR_MANUF_GETNVMEM;
	}

	*return_value = nv_mem[nvmem_datatype];
	return SFX_ERR_MANUF_NONE;
}


sfx_error_t MANUF_API_set_nv_mem(sfx_nvmem_t nvmem_datatype,
                                 sfx_u16 value)
{
	printf("# set_nv_mem(%d, %d)\n", nvmem_datatype, value);
	printf("set_nv_mem %d %d\n", nvmem_datatype, value);

	if(nvmem_datatype >= nv_mem_size) {
		return SFX_ERR_MANUF_SETNVMEM;
	}

	nv_mem[nvmem_datatype] = value;
	return SFX_ERR_MANUF_NONE;
}

sfx_error_t MANUF_API_get_rssi(sfx_s8 *rssi)
{
	printf("# get_rssi(%p)\n", rssi);
	return SFX_ERR_MANUF_NONE;
}

sfx_error_t MANUF_API_wait_frame(sfx_u8 *frame)
{
	printf("# wait_frame(%p)\n", frame);
	return SFX_ERR_MANUF_NONE;
}


sfx_error_t MANUF_API_wait_for_clear_channel ( sfx_u8 cs_min,
                                               sfx_u8 cs_threshold)
{
	printf("# wait_for_clear_channel(%d, %d)\n", cs_min, cs_threshold);
	return SFX_ERR_MANUF_NONE;
}

sfx_error_t MANUF_API_timer_start_carrier_sense(sfx_u16 time_duration_in_ms)
{
	printf("# timer_start_carrier_sense(%d)\n", time_duration_in_ms);
	return SFX_ERR_MANUF_NONE;
}

sfx_error_t MANUF_API_timer_start(sfx_u16 time_duration_in_s)
{
	printf("# timer_start(%d)\n", time_duration_in_s);
	return SFX_ERR_MANUF_NONE;
}

sfx_error_t MANUF_API_timer_stop(void)
{
	printf("# timer_stop()\n");
	return SFX_ERR_MANUF_NONE;
}

sfx_error_t MANUF_API_timer_stop_carrier_sense(void)
{
	printf("# timer_stop_carrier_sense()\n");
	return SFX_ERR_MANUF_NONE;
}

sfx_error_t MANUF_API_timer_wait_for_end(void)
{
	printf("# timer_wait_for_end()\n");
	return SFX_ERR_MANUF_NONE;
}

sfx_error_t MANUF_API_report_test_result(sfx_bool status)
{
	printf("# report_test_result(%d)\n", status);
	return SFX_ERR_MANUF_NONE;
}
