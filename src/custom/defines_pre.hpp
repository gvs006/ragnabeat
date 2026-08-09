// Copyright (c) rAthena Dev Teams - Licensed under GNU GPL
// For more information, see LICENCE in the main folder

#ifndef CONFIG_CUSTOM_DEFINES_PRE_HPP
#define CONFIG_CUSTOM_DEFINES_PRE_HPP

/**
 * rAthena configuration file (http://rathena.org)
 * For detailed guidance on these check http://rathena.org/wiki/SRC/config/
 **/

// Versao do cliente. Definido aqui (e nao em src/config/packets.hpp) porque este
// arquivo e o ponto de customizacao oficial e sobrevive a merges do upstream.
//
// 2025-04-16_Ragexe_1744255909 (build 2025-04-10) - build regional com
// basesdk.dll/iapsdk.dll, que renderiza acentuacao latina (os builds kRO nao).
//
// Par exato com o full client 2025-04-16 usado em KRO-NEW. O 2025-06-04 foi
// testado e produz erro de lua (GetTableIntValueForC) com este data.grf, porque
// o ExternalSettings compilado do GRF e de 2024-08 e nao casa com aquele exe.
#define PACKETVER 20250416

#endif /* CONFIG_CUSTOM_DEFINES_PRE_HPP */
