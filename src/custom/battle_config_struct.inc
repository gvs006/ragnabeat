// Copyright (c) rAthena Dev Teams - Licensed under GNU GPL
// For more information, see LICENCE in the main folder

/**
 * Custom battle config structure
 * Place the definition of custom battle configuration structure members in this file.
 *
 * Make sure that the name you want is not already taken by looking into battle.hpp
 * Do not forget to add initilization logic to battle_config_init.inc
 *
 * Format:
 *	 <datatype> name;
 **/

// Ragnabeat: random option automatico em equipamento dropado.
// Ver mob_getdefault_optgroup() em src/map/mob.cpp e conf/import/battle_conf.txt
int32 randopt_drop_enable;
int32 randopt_drop_group_t1;
int32 randopt_drop_group_t2;
int32 randopt_drop_group_t3;
int32 randopt_drop_t2_minlevel;
int32 randopt_drop_t3_minlevel;
int32 randopt_drop_helm_acc;

