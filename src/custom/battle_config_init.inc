// Copyright (c) rAthena Dev Teams - Licensed under GNU GPL
// For more information, see LICENCE in the main folder

/**
 * Custom battle config initializations
 * Place the definition of custom battle configuration initializations in this file.
 *
 * Do not forget to add a comma at the end of the line, if you want to add another config
 *
 * Format:
 *	 { "name", &battle_config.<variable name>, <default value>, <minimum value>, <maximum value> },
 **/

// Ragnabeat: random option automatico em equipamento dropado.
// Documentacao dos valores em conf/import/battle_conf.txt
{ "randopt_drop_enable",                &battle_config.randopt_drop_enable,             0,      0,      1,              },
{ "randopt_drop_group_t1",              &battle_config.randopt_drop_group_t1,           1,      0,      UINT16_MAX,     },
{ "randopt_drop_group_t2",              &battle_config.randopt_drop_group_t2,           2,      0,      UINT16_MAX,     },
{ "randopt_drop_group_t3",              &battle_config.randopt_drop_group_t3,           3,      0,      UINT16_MAX,     },
{ "randopt_drop_t2_minlevel",           &battle_config.randopt_drop_t2_minlevel,       40,      0,      MAX_LEVEL,      },
{ "randopt_drop_t3_minlevel",           &battle_config.randopt_drop_t3_minlevel,       75,      0,      MAX_LEVEL,      },
{ "randopt_drop_helm_acc",              &battle_config.randopt_drop_helm_acc,           0,      0,      1,              },

