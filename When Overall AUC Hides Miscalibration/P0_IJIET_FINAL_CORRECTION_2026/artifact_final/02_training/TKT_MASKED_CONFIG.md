T-KT masked uses configs/assist2012.yaml together with class TKTc in src/protocol_v2.py.
There is no separate YAML. The mask is causal attention and padding id 2*n_kcs.
simpleKT sensitivity uses configs/assist_simplekt_one_seed.yaml, copied here as simplekt_assist2012.yaml,
and scripts/p0_retrain_official_simplekt.py.
DKT uses configs/assist2012.yaml. Junyi DKT uses configs/junyi.yaml.
