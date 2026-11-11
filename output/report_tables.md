### Counts per chain (to-block fixed per chain; see as-of table)

| chain | chainId | Identity `Registered` | Reputation `NewFeedback` | Validation `ValidationRequest` | Validation `ValidationResponse` | distinct validators (req / resp) |
|---|---|---:|---:|---:|---:|---|
| Ethereum | 1 | 53,903 | 21,337 | 0 | 0 | 0 / 0 |
| Base | 8453 | 110,516 | 554,477 | 15 | 12 | 4 / 4 |
| Optimism | 10 | 565 | 340 | 0 | 0 | 0 / 0 |
| BSC | 56 | NOT MEASURED | NOT MEASURED | NOT MEASURED | NOT MEASURED | — |
| Gnosis | 100 | 4,159 | 4,341 | 0 | 0 | 0 / 0 |
| Polygon | 137 | 686 | 632 | 0 | 0 | 0 / 0 |
| Monad | 143 | 10,389 | 9,328 | 5 | 5 | 3 / 3 |
| XLayer | 196 | — | — | — | — | not measured (no endpoint) |
| Hedera | 295 | — | — | — | — | not measured (no_code_at_to_block) |
| Shape | 360 | 2,098 | 0 | 0 | 0 | 0 / 0 |
| Metis | 1088 | 138 | 0 | 0 | 0 | 0 / 0 |
| Injective | 1776 | — | — | — | — | not measured (unresolved_no_floor) |
| Soneium | 1868 | NOT MEASURED | NOT MEASURED | NOT MEASURED | NOT MEASURED | — |
| GOAT Network | 2345 | 88 | 1 | 0 | 0 | 0 / 0 |
| Abstract | 2741 | 16,918 | 296 | 0 | 0 | 0 / 0 |
| MegaETH | 4326 | 12,727 | 23 | 0 | 0 | 0 / 0 |
| Robinhood Chain | 4663 | 8,784 | 702 | 0 | 0 | 0 / 0 |
| Mantle | 5000 | 144 | 1,699 | 10 | 0 | 2 / 0 |
| 0G | 16661 | 3,882,470 | 20 | 14 | 14 | 1 / 1 |
| Arbitrum One | 42161 | 1,623 | 1,055 | 0 | 0 | 0 / 0 |
| Celo | 42220 | ≥5,944 (lower bound: endpoint returns false-empties) | ≥17,990 (lower bound: endpoint returns false-empties) | ≥21 (lower bound: endpoint returns false-empties) | ≥17 (lower bound: endpoint returns false-empties) | 21 / 17 |
| Avalanche | 43114 | 1,845 | 14,624 | 0 | 0 | 0 / 0 |
| Billions | 45056 | — | — | — | — | not measured (no endpoint) |
| Linea | 59144 | 115 | 31 | 0 | 0 | 0 / 0 |
| Taiko | 167000 | 94 | 0 | 0 | 0 | 0 / 0 |
| Scroll | 534352 | 108 | 0 | 0 | 0 | 0 / 0 |
| SKALE Base | 1187947933 | 2,226 | 10,068 | 0 | 0 | 0 / 0 |

Sum over chains with a *complete* scan only: Registered=4,115,540, NewFeedback=636,964, ValidationRequest=65, ValidationResponse=48

### As-of blocks, deployment blocks, endpoints

| chain | chainId | from-block (validation) | from-block source | to-block | to-block UTC | endpoints that served logs |
|---|---|---:|---|---:|---|---|
| Ethereum | 1 | 24339874 | resolved | 26182323 | 2026-10-13T08:18:23Z | mainnet.gateway.tenderly.co |
| Optimism | 10 | 147514949 | resolved | 158141652 | 2026-10-13T09:01:21Z | optimism.gateway.tenderly.co |
| BSC | 56 | 63036986 | unresolved_no_archive | 127376079 | 2026-10-13T09:08:02Z | — |
| Gnosis | 100 | 44505017 | resolved | 48732735 | 2026-10-13T08:48:20Z | rpc.gnosischain.com |
| Polygon | 137 | 82458489 | resolved | 95451277 | 2026-10-13T09:03:31Z | polygon.gateway.tenderly.co |
| Monad | 143 | 52952798 | resolved | 113001219 | 2026-10-13T09:08:41Z | rpc2.monad.xyz |
| Hedera | 295 | None | no_code_at_to_block | 101067831 | 2026-10-13T09:00:59Z | — |
| Shape | 360 | 25649381 | resolved | 35068820 | 2026-10-13T09:01:51Z | mainnet.shape.network |
| Metis | 1088 | 22161528 | resolved | 23271915 | 2026-10-13T07:13:27Z | andromeda.metis.io |
| Injective | 1776 | None | unresolved_no_floor | 187094908 | 2026-10-13T09:07:53Z | — |
| Soneium | 1868 | 18879204 | resolved | 29373675 | 2026-10-13T09:01:41Z | — |
| GOAT Network | 2345 | 6931867 | unresolved_no_archive | 16054619 | 2026-10-13T08:55:12Z | rpc.goat.network |
| Abstract | 2741 | 39596878 | resolved | 87535983 | 2026-10-13T09:04:00Z | api.mainnet.abs.xyz |
| MegaETH | 4326 | 7833807 | resolved | 29085340 | 2026-10-13T09:05:51Z | mainnet.megaeth.com |
| Robinhood Chain | 4663 | 1 | unresolved_no_archive | 87395843 | 2026-10-13T09:09:57Z | rpc.mainnet.chain.robinhood.com |
| Mantle | 5000 | 91333851 | resolved | 101875890 | 2026-10-13T09:01:32Z | mantle-rpc.publicnode.com |
| Base | 8453 | 41663785 | resolved | 52546365 | 2026-10-13T09:01:17Z | base.gateway.tenderly.co |
| 0G | 16661 | 30941213 | resolved | 47005936 | 2026-10-13T09:06:38Z | evmrpc.0g.ai |
| Arbitrum One | 42161 | 384761330 | unresolved_no_archive | 514383417 | 2026-10-13T09:08:41Z | arb1.arbitrum.io |
| Celo | 42220 | 58396736 | resolved | 79981588 | 2026-10-13T09:05:46Z | forno.celo.org |
| Avalanche | 43114 | 77389011 | resolved | 97432220 | 2026-10-13T09:05:20Z | api.avax.network |
| Linea | 59144 | 28662556 | resolved | 32310196 | 2026-10-13T08:37:21Z | rpc.linea.build |
| Taiko | 167000 | 4305750 | resolved | 12619470 | 2026-10-13T09:01:31Z | taiko-rpc.publicnode.com |
| Scroll | 534352 | 29432421 | resolved | 35358439 | 2026-10-13T08:57:41Z | rpc.scroll.io |
| SKALE Base | 1187947933 | 1 | code_present_at_search_floor | 3072934 | 2026-10-13T08:27:15Z | skale-base.skalenodes.com |

### Positive control: `Initialized(uint64)` seen from from-block (proves log history present)

| chain | identity | reputation | validation |
|---|---:|---:|---:|
| Ethereum | 2 | 2 | 2 |
| Optimism | 2 | 2 | 2 |
| BSC | ERR | ERR | ERR |
| Gnosis | 2 | 2 | 2 |
| Polygon | 2 | 2 | 2 |
| Monad | 2 | 2 | 2 |
| Shape | 2 | 2 | 2 |
| Metis | 2 | 2 | 2 |
| Soneium | ERR | ERR | ERR |
| GOAT Network | 2 | 2 | 2 |
| Abstract | 2 | 2 | 2 |
| MegaETH | 2 | 2 | 2 |
| Robinhood Chain | 2 | 2 | 2 |
| Mantle | 2 | 2 | 2 |
| Base | 2 | 2 | 2 |
| 0G | 2 | 2 | 2 |
| Arbitrum One | 2 | 2 | 2 |
| Celo | 2 | 0 | 0 |
| Avalanche | 2 | 2 | 2 |
| Linea | 2 | 2 | 2 |
| Taiko | 2 | 2 | 2 |
| Scroll | 2 | 2 | 2 |
| SKALE Base | 2 | 2 | 2 |

### Validation events (all chains, raw)

- **Monad** `ValidationRequest`: 5 logs, blocks 106470714–112814384, 3 validator(s); status complete
- **Monad** `ValidationResponse`: 5 logs, blocks 106470718–112814403, 3 validator(s); status complete
- **Mantle** `ValidationRequest`: 10 logs, blocks 96827854–97174516, 2 validator(s); status complete
- **Base** `ValidationRequest`: 15 logs, blocks 43134133–51702363, 4 validator(s); status complete
- **Base** `ValidationResponse`: 12 logs, blocks 43135044–51702366, 4 validator(s); status complete
- **0G** `ValidationRequest`: 14 logs, blocks 38894992–38895428, 1 validator(s); status complete
- **0G** `ValidationResponse`: 14 logs, blocks 38895003–38895440, 1 validator(s); status complete
- **Celo** `ValidationRequest`: 21 logs, blocks 62018062–62055678, 21 validator(s); status complete
- **Celo** `ValidationResponse`: 17 logs, blocks 62018317–62055690, 17 validator(s); status complete
