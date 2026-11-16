# ERC-8004 registry usage, counted from chain logs, as of 13 October 2026

This repository is a measurement of how much the three [ERC-8004](https://eips.ethereum.org/EIPS/eip-8004)
registries (Identity, Reputation, Validation) were used on mainnet chains up to fixed blocks on 13 October 2026. It
counts event logs. The data, the code that produced it and the controls are all here, so the counts can be rerun.

It is read-only. No transaction was sent and no private key was used. Every number comes from `eth_getLogs`,
`eth_getCode`, `eth_getBlockByNumber` or `eth_call` against public, keyless RPC endpoints. The addenda also use
`eth_getStorageAt` and `eth_getTransactionReceipt`.

## Findings in brief

**Denominators: 27 mainnets checked; registry code established on 23; 21 measured; 5 with at least one validation request (Base, Mantle, 0G, Celo, Monad). Not measured (6): BSC (code presence not established: HTTP 403), XLayer and Billions (no public endpoint passed the log smoke test; code presence not established), Soneium (code present; HTTP 403 on log scans), Injective (code present; history pruned), Hedera (no code at the three registry addresses).**

1. **Base's validation activity is one burst.** 12 of Base's 15 `ValidationRequest` logs came from **one agent on 9–10
   March 2026**. There was then one request in August and two in September, and **none in October** up to the as-of
   block (13 October, 09:01 UTC). See [addendum A](ADDENDUM-2026-11-11-base-request-dates.md).
2. **Across the 21 measured chains**, the Validation registry emitted **65 `ValidationRequest` and 48 `ValidationResponse`
   logs, on 5 chains** (Celo, Base, 0G, Mantle, Monad). Ethereum mainnet had none. Over the same chains and blocks there
   were at least 636,964 Reputation `NewFeedback` logs. Celo's figures are lower bounds, and Celo is in every total, so
   all totals are lower bounds.
3. **Self-validation dominates where validation is used, except on Celo.** At the block of each request, the named
   validator was the owner of the requesting agent for 14 of 15 requests on Base, 10 of 10 on Mantle and 14 of 14 on 0G.
   It was 2 of 5 on Monad and 0 of 21 on Celo. The
   [per-chain table](#who-validates) shows both reads and what they can and cannot show.

## What was measured

- **Contracts:** the three ERC-8004 registry proxies at their CREATE2 mainnet addresses, which are the same on every
  chain:

  | registry | address |
  |---|---|
  | Identity | `0x8004A169FB4a3325136EB29fA0ceB6D2e539a432` |
  | Reputation | `0x8004BAa17C55a88189AE136b182e5fdA19dE9b63` |
  | Validation | `0x8004Cc8439f36fd5F9F049D9fF86523Df6dAAB58` |

- **Chains:** the 27 mainnets that the reference implementation lists. Of these, 21 were measured completely. The other
  six could not be measured and are listed in [Limits](#limits).
- **Events:** Identity `Registered`, Reputation `NewFeedback`, Validation `ValidationRequest` and `ValidationResponse`.
  `Initialized(uint64)` on all three proxies was also counted, as a positive control.
- **Range:** for each chain and registry, from the block where the proxy was deployed to a fixed as-of block. The as-of
  block was `head − 256` (a reorg margin), fixed between 09:09:49 and 09:10:28 UTC on **13 October 2026**, before any
  counting. The as-of block for each chain is in the results table and in `output/as_of.json`.

## Method

1. **Addresses** come from the reference implementation,
   [`erc-8004/erc-8004-contracts`](https://github.com/erc-8004/erc-8004-contracts) at commit
   `b9e466c250744a7e06b13dff9d3c2844ed64f825` (master on 2026-10-13, committed 2026-08-15), `scripts/addresses.ts`,
   `MAINNET_ADDRESSES`. The file is vendored as `abis/addresses.ts.vendored`, with hashes in `abis/PROVENANCE.json`.
   The reference README lists the Identity and Reputation addresses per chain but no Validation address. The
   Validation address therefore comes from `addresses.ts` only. No address was taken from the specification text.
2. **Chain list:** `addresses.ts` `MAINNET_CHAIN_IDS`, plus four chains that the reference README lists but
   `addresses.ts` does not: Robinhood Chain, Billions, Injective and 0G. Their chain IDs were resolved by name from
   chainid.network, which is not authoritative. See `PROVENANCE-chain-list.md`.
3. **Event topics** are computed from the ABI JSON files in the reference repository at the same commit
   (`abis/*.json`), **not from deployed bytecode** or verified source, and never typed by hand. The four topic0 values
   are pinned in the self-test to values computed independently with Foundry's `cast keccak`. One check against a
   deployment was added later: on Base, the implementation behind the Validation proxy contains the function selectors
   of the ABI's three validation functions ([addendum B](ADDENDUM-2026-11-11-base-registry-address.md)). Event topics
   cannot be checked that way, because events have no dispatcher entry.

   | event | signature | topic0 |
   |---|---|---|
   | Identity `Registered` | `Registered(uint256,string,address)` | `0xca52e62c367d81bb2e328eb795f7c7ba24afb478408a26c0e201d155c449bc4a` |
   | Reputation `NewFeedback` | `NewFeedback(uint256,address,uint64,int128,uint8,string,string,string,string,string,bytes32)` | `0x6a4a61743519c9d648a14e6493f47dbe3ff1aa29e7785c96c8326a205e58febc` |
   | `ValidationRequest` | `ValidationRequest(address,uint256,string,bytes32)` | `0x530436c3634a98e1e626b0898be2f1e9980cc1bd2a78c07a0aba52d0a48a5059` |
   | `ValidationResponse` | `ValidationResponse(address,uint256,bytes32,uint8,string,bytes32,string)` | `0xafddf629e874ccc3963b6a888c477bd464a6c8525024fc88759ea3b2326349ae` |
   | positive control | `Initialized(uint64)` | `0xc7f505b2f371ae2175ee4913f4499e1f2633a7b5936321eed1cdaeb6115181d2` |

4. **Deploy (from-) blocks were found by on-chain binary search.** They were not taken from the specification or the
   reference implementation. The search used `eth_getCode`, between the first block on or after 2025-10-01 and the as-of block. Each result was then
   cross-checked: no code one block earlier, code at the block, and the proxy-initialisation logs at the block. Where an
   endpoint had no archive state (`unresolved_no_archive`), the scan started at the first block on or after 2025-10-01
   instead. Where code was already present at that floor (`code_present_at_search_floor`, SKALE Base only), the floor
   was used. The value and how it was fixed are recorded per chain and registry in `output/deploy_blocks.json`.
5. **Counting:** `eth_getLogs` per registry and event, filtered by address and topic0, in adaptively sized block chunks.
   - A sub-range that cannot be fetched raises an error. It is never counted as zero.
   - A response whose length equals a common provider cap (1,000, 1,500, 2,000, 5,000, 10,000 …) is split and re-fetched.
   - Every returned log is re-checked against the requested address, topic0 and block range.
   - Duplicates by (block, log index) are dropped. None were observed.
   - `ValidationRequest` and `ValidationResponse` are fetched in one OR-topic scan and split by topic0. Every validation
     log is stored raw in `output/counts/<chainId>_validation_*.json`.
6. **Time budgets:** a scan that hit its wall-clock budget was marked `INCOMPLETE_BUDGET`. `finish` later resumed it
   over only the uncovered sub-ranges. Every count in the results table is from a scan with status `complete`.
7. **Celo:** the endpoint returned false-empty results, so the Validation scan was repeated and the union of distinct
   logs over three passes was taken (`union`). A union can only move towards the true set. The Celo result is still
   labelled a lower bound.
8. **Owners:** read twice, at different times. See [Who validates](#who-validates).

## Controls

Before counting, each chain–event pair had two negative controls, and each had to return **zero**:

- **(a) pre-deployment:** the same scan over the 200,000 blocks immediately before the deploy block.
- **(b) corrupted topic0:** the same scan with the last hex digit of topic0 flipped (`…5059` → `…5050`). For the
  validation pair, both topics were corrupted together.

A third count, **(b′)**, gives the **true** topic0 over the same window as (b). Where (b′) is non-zero, the window
contained real events, so a zero in (b) is informative.

**Windowed controls.** On the larger chains, (b) and (b′) did not cover the full range. They covered a window from the
deploy block of at most 600 calls' worth of blocks, capped at 12,000,000 blocks. Such rows are marked "no (window)"
below. The windowed chains are Base (600,000-block window), Polygon, Monad, Abstract, MegaETH, Robinhood Chain, 0G,
Arbitrum One, Celo and Avalanche. The `cmd_controls` docstring in the code still says "3,000 calls". The constant
actually used is `CONTROL_WINDOW_CALLS = 600`.

**Summary: 59 distinct control sets passed.** There were 69 sets in all: 3 each on the 23 chains whose deploy check allowed a scan, which are the 21 measured chains plus BSC and Soneium. None returned non-zero.
Seven hit their time budget and are reported as incomplete, not passed: all three on Shape, all three on SKALE Base,
and 0G `Registered`. Three errored: BSC, which has no public endpoint for historical logs. `output/controls.json` holds
61 pass records for the 59 distinct sets, because 0G's validation and `NewFeedback` sets ran in both parts of the
control run with identical results. Robinhood Chain's part-1 lines did not match the merge pattern (`mergecontrols`):
the chain name is wider than its log column. Only its part-2 results are in `controls.json`. The part-1 values,
verbatim in `output/controls_part1.stdout`, are identical.

Points to weigh:

- **Shape and SKALE Base have no passing control.** Their partial controls returned 0 for (a) and (b) over the range
  they covered. Their counts later completed in full. The totals are given [with and without them](#results). Neither
  chain has any validation event, so the validation totals are the same either way.
- **No (a) control was possible** where the deploy block was not resolved: GOAT Network, Robinhood Chain, Arbitrum One
  and SKALE Base.
- **(b′) = 0 in the window** for every validation pair except Mantle and 0G. For all of Arbitrum One and Robinhood
  Chain, (b′) is 0 too. There, (b) = 0 says only that an empty window stayed empty.

Verbatim output: `output/controls_part1.stdout` and `output/controls_part2.stdout`. Merged record:
`output/controls.json`.

| chain | event(s) | (a) pre-deploy range → count | (b) corrupted topic0 window → count | full range? | (b′) true topic0, same window |
|---|---|---|---|---|---:|
| Ethereum | NewFeedback | [24139873, 24339872] → 0 | [24339873, 26182323] → 0 | yes | 21337 |
| Ethereum | Registered | [24139871, 24339870] → 0 | [24339871, 26182323] → 0 | yes | 53903 |
| Ethereum | Validation (both) | [24139874, 24339873] → 0 | [24339874, 26182323] → 0 | yes | 0 |
| Base | NewFeedback | [41463784, 41663783] → 0 | [41663784, 42263784] → 0 | no (window) | 12677 |
| Base | Registered | [41463783, 41663782] → 0 | [41663783, 42263783] → 0 | no (window) | 17956 |
| Base | Validation (both) | [41463785, 41663784] → 0 | [41663785, 42263785] → 0 | no (window) | 0 |
| Optimism | NewFeedback | [147314948, 147514947] → 0 | [147514948, 158141652] → 0 | yes | 340 |
| Optimism | Registered | [147314947, 147514946] → 0 | [147514947, 158141652] → 0 | yes | 565 |
| Optimism | Validation (both) | [147314949, 147514948] → 0 | [147514949, 158141652] → 0 | yes | 0 |
| BSC | all three | ERROR | ERROR: HTTP 403 at block 63036986, no historical logs | — | — |
| Gnosis | NewFeedback | [44305016, 44505015] → 0 | [44505016, 48732735] → 0 | yes | 4341 |
| Gnosis | Registered | [44305010, 44505009] → 0 | [44505010, 48732735] → 0 | yes | 4159 |
| Gnosis | Validation (both) | [44305017, 44505016] → 0 | [44505017, 48732735] → 0 | yes | 0 |
| Polygon | NewFeedback | [82258486, 82458485] → 0 | [82458486, 94458486] → 0 | no (window) | 500 |
| Polygon | Registered | [82258484, 82458483] → 0 | [82458484, 94458484] → 0 | no (window) | 675 |
| Polygon | Validation (both) | [82258489, 82458488] → 0 | [82458489, 94458489] → 0 | no (window) | 0 |
| Monad | NewFeedback | [52752794, 52952793] → 0 | [52952794, 58952794] → 0 | no (window) | 9009 |
| Monad | Registered | [52752790, 52952789] → 0 | [52952790, 58952790] → 0 | no (window) | 8359 |
| Monad | Validation (both) | [52752798, 52952797] → 0 | [52952798, 58952798] → 0 | no (window) | 0 |
| Shape | NewFeedback | → 0 (partial) | [25649379, 35068820] → 0 (partial) | INCOMPLETE (time budget) | ≥0 |
| Shape | Registered | → 0 (partial) | [25649378, 35068820] → 0 (partial) | INCOMPLETE (time budget) | ≥1904 |
| Shape | Validation (both) | → 0 (partial) | [25649381, 35068820] → 0 (partial) | INCOMPLETE (time budget) | ≥0 |
| Metis | NewFeedback | [21961527, 22161526] → 0 | [22161527, 23271915] → 0 | yes | 0 |
| Metis | Registered | [21961525, 22161524] → 0 | [22161525, 23271915] → 0 | yes | 138 |
| Metis | Validation (both) | [21961528, 22161527] → 0 | [22161528, 23271915] → 0 | yes | 0 |
| Soneium | NewFeedback | [18679201, 18879200] → 0 | [18879201, 29373675] → 0 | yes | 0 |
| Soneium | Registered | [18679198, 18879197] → 0 | [18879198, 29373675] → 0 | yes | 0 |
| Soneium | Validation (both) | [18679204, 18879203] → 0 | [18879204, 29373675] → 0 | yes | 0 |
| GOAT Network | NewFeedback | n/a (no resolved deploy block) | [6931867, 16054619] → 0 | yes | 1 |
| GOAT Network | Registered | n/a (no resolved deploy block) | [6931867, 16054619] → 0 | yes | 88 |
| GOAT Network | Validation (both) | n/a (no resolved deploy block) | [6931867, 16054619] → 0 | yes | 0 |
| Abstract | NewFeedback | [39396875, 39596874] → 0 | [39596875, 51596875] → 0 | no (window) | 131 |
| Abstract | Registered | [39396871, 39596870] → 0 | [39596871, 51596871] → 0 | no (window) | 713 |
| Abstract | Validation (both) | [39396878, 39596877] → 0 | [39596878, 51596878] → 0 | no (window) | 0 |
| MegaETH | NewFeedback | [7633806, 7833805] → 0 | [7833806, 19833806] → 0 | no (window) | 23 |
| MegaETH | Registered | [7633805, 7833804] → 0 | [7833805, 19833805] → 0 | no (window) | 12727 |
| MegaETH | Validation (both) | [7633807, 7833806] → 0 | [7833807, 19833807] → 0 | no (window) | 0 |
| Robinhood Chain | NewFeedback | n/a (no resolved deploy block) | [1, 12000001] → 0 | no (window) | 0 |
| Robinhood Chain | Registered | n/a (no resolved deploy block) | [1, 12000001] → 0 | no (window) | 0 |
| Robinhood Chain | Validation (both) | n/a (no resolved deploy block) | [1, 12000001] → 0 | no (window) | 0 |
| Mantle | NewFeedback | [91133848, 91333847] → 0 | [91333848, 101875890] → 0 | yes | 1699 |
| Mantle | Registered | [91133846, 91333845] → 0 | [91333846, 101875890] → 0 | yes | 144 |
| Mantle | Validation (both) | [91133851, 91333850] → 0 | [91333851, 101875890] → 0 | yes | 10 |
| 0G | NewFeedback | [30741196, 30941195] → 0 | [30941196, 42941196] → 0 | no (window) | 10 |
| 0G | Registered | → 0 (partial) | [30941187, 42941187] → 0 (partial) | INCOMPLETE (time budget) | ≥433016 |
| 0G | Validation (both) | [30741213, 30941212] → 0 | [30941213, 42941213] → 0 | no (window) | 28 |
| Arbitrum One | NewFeedback | n/a (no resolved deploy block) | [384761330, 396761330] → 0 | no (window) | 0 |
| Arbitrum One | Registered | n/a (no resolved deploy block) | [384761330, 396761330] → 0 | no (window) | 0 |
| Arbitrum One | Validation (both) | n/a (no resolved deploy block) | [384761330, 396761330] → 0 | no (window) | 0 |
| Celo | NewFeedback | [58196729, 58396728] → 0 | [58396729, 61396729] → 0 | no (window) | 1190 |
| Celo | Registered | [58196724, 58396723] → 0 | [58396724, 61396724] → 0 | no (window) | 1082 |
| Celo | Validation (both) | [58196736, 58396735] → 0 | [58396736, 61396736] → 0 | no (window) | 0 |
| Avalanche | NewFeedback | [77189003, 77389002] → 0 | [77389003, 89389003] → 0 | no (window) | 14374 |
| Avalanche | Registered | [77189000, 77388999] → 0 | [77389000, 89389000] → 0 | no (window) | 1771 |
| Avalanche | Validation (both) | [77189011, 77389010] → 0 | [77389011, 89389011] → 0 | no (window) | 0 |
| Linea | NewFeedback | [28462554, 28662553] → 0 | [28662554, 32310196] → 0 | yes | 31 |
| Linea | Registered | [28462553, 28662552] → 0 | [28662553, 32310196] → 0 | yes | 115 |
| Linea | Validation (both) | [28462556, 28662555] → 0 | [28662556, 32310196] → 0 | yes | 0 |
| Taiko | NewFeedback | [4105749, 4305748] → 0 | [4305749, 12619470] → 0 | yes | 0 |
| Taiko | Registered | [4105747, 4305746] → 0 | [4305747, 12619470] → 0 | yes | 94 |
| Taiko | Validation (both) | [4105750, 4305749] → 0 | [4305750, 12619470] → 0 | yes | 0 |
| Scroll | NewFeedback | [29232418, 29432417] → 0 | [29432418, 35358439] → 0 | yes | 0 |
| Scroll | Registered | [29232417, 29432416] → 0 | [29432417, 35358439] → 0 | yes | 108 |
| Scroll | Validation (both) | [29232421, 29432420] → 0 | [29432421, 35358439] → 0 | yes | 0 |
| SKALE Base | NewFeedback | not run (code at search floor) | [1, 1200001] → 0 (partial) | INCOMPLETE (time budget) | ≥6082 |
| SKALE Base | Registered | not run (code at search floor) | [1, 1200001] → 0 (partial) | INCOMPLETE (time budget) | ≥208 |
| SKALE Base | Validation (both) | not run (code at search floor) | [1, 1200001] → 0 (partial) | INCOMPLETE (time budget) | ≥0 |

**Positive control.** `Initialized(uint64)` must appear from the from-block of each proxy, which shows that the
endpoint serves log history there. It returned 2 on all three proxies of every measured chain except Celo. On Celo it
returned 2 for Identity and 0 for Reputation and Validation. This is the endpoint's false-empty behaviour, not evidence
that those proxies were never initialised. A separate known-positive test is in `output/endpoint_consistency.txt`
(code: `inline/2026-10-13T1716Z_endpoint_consistency_part1.py` and `…part2.py`). It queried each serving endpoint 15
times per registry at the deploy block, where 3 logs are known to exist. For the four chains without a resolved deploy
block, it used the block of the first `Initialized` log instead. Every endpoint returned the expected logs on every
call, except `forno.celo.org`, which returned 0 in 17 of 45 calls.

## Results

Every count is from a complete scan from the from-block to the as-of block. "Distinct validators" counts distinct
topic1 addresses of the logs. Celo values are lower bounds (≥).

| chain | chainId | as-of (to) block | to-block UTC | `ValidationRequest` | `ValidationResponse` | distinct validators (req / resp) | `Registered` | `NewFeedback` |
|---|---:|---:|---|---:|---:|---|---:|---:|
| Ethereum | 1 | 26182323 | 2026-10-13T08:18:23Z | 0 | 0 | 0 / 0 | 53,903 | 21,337 |
| Base | 8453 | 52546365 | 2026-10-13T09:01:17Z | 15 | 12 | 4 / 4 | 110,516 | 554,477 |
| Optimism | 10 | 158141652 | 2026-10-13T09:01:21Z | 0 | 0 | 0 / 0 | 565 | 340 |
| Gnosis | 100 | 48732735 | 2026-10-13T08:48:20Z | 0 | 0 | 0 / 0 | 4,159 | 4,341 |
| Polygon | 137 | 95451277 | 2026-10-13T09:03:31Z | 0 | 0 | 0 / 0 | 686 | 632 |
| Monad | 143 | 113001219 | 2026-10-13T09:08:41Z | 5 | 5 | 3 / 3 | 10,389 | 9,328 |
| Shape | 360 | 35068820 | 2026-10-13T09:01:51Z | 0 | 0 | 0 / 0 | 2,098 | 0 |
| Metis | 1088 | 23271915 | 2026-10-13T07:13:27Z | 0 | 0 | 0 / 0 | 138 | 0 |
| GOAT Network | 2345 | 16054619 | 2026-10-13T08:55:12Z | 0 | 0 | 0 / 0 | 88 | 1 |
| Abstract | 2741 | 87535983 | 2026-10-13T09:04:00Z | 0 | 0 | 0 / 0 | 16,918 | 296 |
| MegaETH | 4326 | 29085340 | 2026-10-13T09:05:51Z | 0 | 0 | 0 / 0 | 12,727 | 23 |
| Robinhood Chain | 4663 | 87395843 | 2026-10-13T09:09:57Z | 0 | 0 | 0 / 0 | 8,784 | 702 |
| Mantle | 5000 | 101875890 | 2026-10-13T09:01:32Z | 10 | 0 | 2 / 0 | 144 | 1,699 |
| 0G | 16661 | 47005936 | 2026-10-13T09:06:38Z | 14 | 14 | 1 / 1 | 3,882,470 | 20 |
| Arbitrum One | 42161 | 514383417 | 2026-10-13T09:08:41Z | 0 | 0 | 0 / 0 | 1,623 | 1,055 |
| Celo | 42220 | 79981588 | 2026-10-13T09:05:46Z | ≥21 | ≥17 | ≥21 / ≥17 | ≥5,944 | ≥17,990 |
| Avalanche | 43114 | 97432220 | 2026-10-13T09:05:20Z | 0 | 0 | 0 / 0 | 1,845 | 14,624 |
| Linea | 59144 | 32310196 | 2026-10-13T08:37:21Z | 0 | 0 | 0 / 0 | 115 | 31 |
| Taiko | 167000 | 12619470 | 2026-10-13T09:01:31Z | 0 | 0 | 0 / 0 | 94 | 0 |
| Scroll | 534352 | 35358439 | 2026-10-13T08:57:41Z | 0 | 0 | 0 / 0 | 108 | 0 |
| SKALE Base | 1187947933 | 3072934 | 2026-10-13T08:27:15Z | 0 | 0 | 0 / 0 | 2,226 | 10,068 |
| BSC | 56 | 127376079 | 2026-10-13T09:08:02Z | not measured | not measured | — | not measured | not measured |
| XLayer | 196 | — | — | not measured | not measured | — | not measured | not measured |
| Hedera | 295 | 101067831 | 2026-10-13T09:00:59Z | no code at any of the three addresses | — | — | — | — |
| Injective | 1776 | 187094908 | 2026-10-13T09:07:53Z | not measured | not measured | — | not measured | not measured |
| Soneium | 1868 | 29373675 | 2026-10-13T09:01:41Z | not measured | not measured | — | not measured | not measured |
| Billions | 45056 | — | — | not measured | not measured | — | not measured | not measured |

**Totals** (lower bounds, because Celo is included). The second column leaves out Shape and SKALE Base, the two
chains with no passing control.

| | all 21 measured chains | 19 chains with at least one passing control |
|---|---:|---:|
| `ValidationRequest` | 65 | 65 |
| `ValidationResponse` | 48 | 48 |
| `NewFeedback` | 636,964 | 626,896 |
| `Registered` | 4,115,540 | 4,111,216 |

- **Requests by chain:** Celo 21, Base 15, 0G 14, Mantle 10, Monad 5.
- **Responses by chain:** Celo 17, 0G 14, Base 12, Monad 5. Mantle's 10 requests have no response.
- **`Registered`:** 0G alone has 3,882,470.

**Ethereum mainnet: zero `ValidationRequest` and zero `ValidationResponse`** between the Validation proxy's deployment
(block 24,339,874) and block 26,182,323.

From-blocks, and how each was fixed, are in `output/deploy_blocks.json`. `output/report_tables.md` holds the tables as
the scanner's `report` command generated them.

## Who validates

For every logged `ValidationRequest`, the named validator was compared with the owner of the requesting agent. The owner
was read at two different times. Both are reported, and neither replaces the other.

**How "owner" was determined.**

- `validator` is topic1 of the `ValidationRequest` log, and `agentId` is topic2. `owner` is the return value of
  `ownerOf(agentId)` (selector `0x6352211e`) on the Identity registry `0x8004A169FB4a3325136EB29fA0ceB6D2e539a432` of
  the same chain. Addresses are compared case-insensitively.
- **Latest read (13 October 2026), all five chains.** `eth_call` at block tag `"latest"`, at **about 13:57 UTC on
  13 October 2026**, against the endpoints used for the counts. That is neither the block of the request nor the as-of
  block: it is 4 h 48 min to 4 h 56 min after the five chains' as-of blocks (09:01–09:09 UTC). No lookup failed. The
  code, run inline at the time and kept verbatim, is `inline/2026-10-13T1356Z_self_validation_check.py`. Results are in
  `output/self_validation_check.json`.
- **Request-block read (11 November 2026), all five chains.** `eth_call` at each request's own block number (the state
  after that block), on every listed public endpoint. A request counts as determined only if at least two endpoints
  answered and agreed. All 65 requests were determined. See
  [addendum C](ADDENDUM-2026-11-11-owner-at-request-block.md).

| chain | requests | responses | distinct validators (requests) | validator = owner, latest read on 13 Oct | validator = owner at the request block |
|---|---:|---:|---:|---:|---:|
| Base | 15 | 12 | 4 | 14 of 15 | 14 of 15 |
| Mantle | 10 | 0 | 2 | 10 of 10 | 10 of 10 |
| 0G | 14 | 14 | 1 | 10 of 14 | **14 of 14** |
| Monad | 5 | 5 | 3 | 2 of 5 | 2 of 5 |
| Celo (lower bound) | ≥21 | ≥17 | ≥21 | 0 of 21 | 0 of 21 |
| the other 16 measured chains | 0 | 0 | 0 | — | — |

- **0G:** the two reads differ. At the request block, all 14 requests named the agent's then-owner as validator. Four
  agents were transferred afterwards, before the 13 October read.
- **Base:** the one non-match at both times is agent 60102 at block 50,073,293.
- **Celo:** one agent (agentId 1870) named 21 distinct validators, and none was its owner at either time.

**What these reads can and cannot show.**

- **The latest read** shows who held each agent token at about 13:57 UTC on 13 October, not when the request was made.
  The 0G rows show how far that can drift.
- **The request-block read** shows who held the token in the state right after the request's block. That is the closest
  on-chain answer to "did the agent's owner name itself as validator", though a transfer later in the same block would
  still be missed.
- **Neither read** shows whether a validator and an owner are the same person or organisation. A match is consistent
  with an agent validating itself. A non-match does not show independence, because one operator can control several
  addresses. Neither read says anything about the content or quality of a response.

## Credit: Marsel Sultanov's count

The question came from a public count by **Marsel Sultanov** on Ethereum Magicians, in topic 27902
(*ERC-8183: Agentic Commerce*):

- post [#393](https://ethereum-magicians.org/t/erc-8183-agentic-commerce/27902/393), 2026-08-19: "ValidationRegistry
  across both mainnets: 12 requests, 7 responses, one validator — on a single agent, whose validator is its own owner."
- post [#401](https://ethereum-magicians.org/t/erc-8183-agentic-commerce/27902/401), 2026-08-31: "across 96,475 agents
  and 419,155 reputation events, I found 12 validation requests and 7 responses, with one validator."

His figures cover Ethereum mainnet and Base, indexed on 23–24 July 2026. The run history (`RESEARCH.md`) in his
`erc8004-forensics` repository, as read on 2026-10-13, lists Ethereum blocks 24,339,800–25,601,554 and Base blocks
42,003,733–49,019,181 for his final run, plus an earlier Base start at block 41,663,733.

**His figures reproduce exactly with this counter**, over his chains and ranges (`output/replication.json`,
`output/base_pre_author_window.json`):

| | his figure | this counter | range |
|---|---:|---:|---|
| Ethereum `Registered` / `NewFeedback` / requests / responses | 36,778 / 3,203 / 0 / 0 | 36,778 / 3,203 / 0 / 0 | 24,339,800–25,601,554 |
| Base requests / responses / validators / agents | 12 / 7 / 1 / 1 | 12 / 7 / 1 / 1 | 42,003,733–49,019,181 |
| Base `Registered` | 59,697 | 42,949 + 16,748 = 59,697 | final window + launch week from the deploy block (41,663,783) |
| Base `NewFeedback` | 415,952 | 404,811 + 11,141 = 415,952 | final window + launch week from the deploy block (41,663,784) |
| agents, Ethereum + Base | 96,475 | 36,778 + 59,697 = 96,475 | as above |
| feedback events, Ethereum + Base | 419,155 | 3,203 + 415,952 = 419,155 | as above |

The Base `Registered` and `NewFeedback` figures match only when the range starts at the deploy block. The differences
between his figures and the 13 October results come from **time and scope**, not method. Base gained 3 requests and 5
responses after his last indexed block, and validation events also exist on Celo, 0G, Mantle and Monad, which he did not
scan.

## Limits

- **Six of the 27 chains were not measured.** For five of them, usage is **unknown, not zero**. For Hedera, there is
  nothing at these addresses.
  - **BSC:** the only endpoint that passed the smoke test refused historical calls with HTTP 403. The deploy-block
    search failed, and whether code is present was not established.
  - **Soneium:** code is present and the deploy block was resolved. The only endpoint answered the control scans, but it
    returned HTTP 403 at the first block of every count scan.
  - **Injective:** code is present at the as-of block, but the endpoints had pruned the history needed to find a start
    block ("null block").
  - **XLayer and Billions:** no public endpoint passed the `eth_getLogs` smoke test, so even code presence is unknown.
  - **Hedera:** none of the three addresses has code at the as-of block, so there is nothing to count at them. A
    deployment at other addresses would not be seen.
- **Celo is a lower bound.** `forno.celo.org` returned false-empty results for known-positive queries in 17 of 45
  control calls, and one full repeat pass returned 0 logs. Celo's figures are the union of three passes, so the real
  values can only be higher. Every total that includes Celo is therefore a lower bound too.
- **Owner timing.** The original owner read is at `latest`, about 13:57 UTC on 13 October 2026, not at the as-of
  block. [Addendum C](ADDENDUM-2026-11-11-owner-at-request-block.md) adds the owner at each request's own block for
  all 65 requests on the five chains with validation requests.
- **Only the listed addresses.** A registry at another address is invisible to this measurement: a fork, a private
  deployment, a different address on some chain, or the second Validation proxy on Ethereum and Base discussed in
  [addendum B](ADDENDUM-2026-11-11-base-registry-address.md).
- **Controls:** windowed on the largest chains, incomplete for Shape, SKALE Base and 0G `Registered`, and weak where
  the window held no real events. See [Controls](#controls).
- **One endpoint per chain** served most scans. The endpoints were cross-checked by the known-positive test, but no
  full scan was repeated on a second provider, except Celo's union passes.
- **Testnets** were not measured. Their addresses differ.
- **Counts are not value.** A `NewFeedback` log costs gas but carries no stake, and one `Registered` is emitted per
  agent token. Counts say nothing about the quality, truth or economic weight of any signal.

## Defects found in the scanner during the run

All were fixed before the counts in this repository were produced. **Only one regression test was watched failing:**
the slow-path test for #4, against a scratch copy with the bug put back. The `Rpc` presence check for #3 was **not**
watched failing. Defect #2 is covered only indirectly. Defects #1 and #5 have no test, and #6 is endpoint behaviour
handled by data checks rather than a unit test.

| # | defect | regression test that now covers it | watched failing? |
|---:|---|---|---|
| 1 | TLS: Python `urllib` could not verify certificates with the local CA store (`CERTIFICATE_VERIFY_FAILED`), so every chain showed "no working RPC". Fixed by using `certifi`'s CA bundle, not by disabling verification. | **None.** The self-test uses a mock provider and makes no network calls. | Not as a test. The failure was observed on every endpoint during the run but is not preserved in `output/`. |
| 2 | ABI files are JSON lists, but they were loaded as dicts, so every event selection failed. | **Indirect only:** the self-test's topic0 pins call `event_sig`, which loads the ABI files and accepts both shapes. There is no explicit list-versus-dict test. | No. There is no record of the self-test failing on this defect. |
| 3 | An edit deleted `class Rpc`. The self-test still passed, because the mock never used `Rpc`. 69 control sets then failed with `NameError: name 'Rpc' is not defined`. | `selftest` now instantiates `Rpc` and fails if it is missing. | **No.** The assertion was added together with the restored class, and it was never run against the broken code. |
| 4 | The slow-call detector computed `ceiling = end − p + 1` after `p` had advanced. That produced `fromBlock > toBlock` calls and a single-block crawl. | `selftest` forces every call to count as slow (`SLOW_CALL_S = −1`). It requires all 500 logs, fewer than 400 calls and no splits. | **Yes.** The bug was reintroduced in a scratch copy. The self-test then printed `FAIL-SLOWPATH 500 340001 0` and `selftest: FAIL`. |
| 5 | Rate-limit (HTTP 429) handling first subdivided ranges, the wrong direction, and later over-throttled. It was replaced with in-place backoff and gentle per-host pacing. | **None.** The mock provider never returns HTTP errors. | No. |
| 6 | `forno.celo.org` returns false-empty results nondeterministically. This is endpoint behaviour, not scanner code. It was found because the `Initialized` positive control disagreed with an earlier record. | **No unit test.** It is handled by the 45-query known-positive check (`output/endpoint_consistency.txt`), by the `union` passes and by labelling Celo a lower bound (`LOWER_BOUND_CHAINS`). | Yes, as data: 17 false-empty results in 45 calls. |

Also unrepaired in the code as published, with no effect on the counts:

- the `cmd_controls` docstring says 3,000 calls where the code uses 600;
- the `mergecontrols` pattern does not parse log lines whose chain name overflows its column. This affects Robinhood
  Chain, which part 2 re-ran.

## How to rerun

**Requirements.**

- Python 3.9 or later, with `certifi` and `web3`. `web3` is used only for keccak.
- Versions installed on the machine that made the run (as of 2026-11-11): Python 3.13.6, web3 7.16.0, certifi 2026.01.04.
- Foundry's `cast` is optional, for checking the pinned topic0 values independently.
- **No environment variables and no API keys are needed.** All endpoints are public and keyless. The ones used are
  recorded in `output/rpc_selection.json`.

```sh
pip install certifi web3
python3 -I erc8004_usage.py selftest          # must print "selftest: PASS"
```

Every command below writes into `output/`. Run them in a clone, then use `git diff` or `git status` to compare your
results with the recorded ones.

**A. Recount at the recorded as-of blocks** (checks the published numbers). This keeps `output/as_of.json`,
`output/deploy_blocks.json`, `output/rpc_selection.json` and `output/controls.json`:

```sh
python3 -I erc8004_usage.py count --force                       # all chains; or e.g. --chains 8453,5000
python3 -I erc8004_usage.py finish                               # resume any scan that hit its time budget
python3 -I erc8004_usage.py union --chains 42220 --passes 2      # Celo: union of repeat passes
python3 -I erc8004_usage.py report > output/report_tables.md
python3 -I inline/2026-10-13T1356Z_self_validation_check.py      # owners at "latest": reflects today's owners
git diff --stat output/
```

To rerun the controls as well, run `python3 -I erc8004_usage.py controls` before `count`. This overwrites
`output/controls.json`. `count` refuses to run if any control returned non-zero.

**B. A fresh measurement at a new as-of block.** `output/chainlist.json` is not in this repository
([why](PROVENANCE-chain-list.md)). Without it, `select` downloads today's list from chainid.network. To start from the
same candidate endpoints as the 13 October run instead, first fetch the pinned version and check its hash with the
two-line command at the top of `PROVENANCE-chain-list.md`.

```sh
python3 -I erc8004_usage.py select      # uses output/chainlist.json if present, otherwise downloads today's list
python3 -I erc8004_usage.py asof        # fixes NEW as-of blocks (head - 256)
python3 -I erc8004_usage.py deploy
python3 -I erc8004_usage.py ranges
python3 -I erc8004_usage.py controls
python3 -I erc8004_usage.py count --force
python3 -I erc8004_usage.py finish
python3 -I erc8004_usage.py union --chains 42220 --passes 2
python3 -I erc8004_usage.py replicate   # optional: Marsel Sultanov's ranges
python3 -I erc8004_usage.py report > output/report_tables.md
```

The `inline/` scripts must be run from the repository root. They import `erc8004_usage` from the current directory.

The addenda can be rerun from the repository root with read-only calls, in a few minutes each. Each script's docstring
gives its usage. Write the output to a new path to compare it with the recorded file:

```sh
python3 -I addenda/2026-11-11_base_calls.py . /tmp/base_calls.json                     # addenda A and B
python3 -I addenda/2026-11-11_selector_check.py abis/ValidationRegistry.json /tmp/base_calls.json
python3 -I addenda/2026-11-11_owner_at_request_block.py /tmp/owner_at_request_block.json  # addendum C
```

**Expected runtime** on public endpoints: several hours. The recorded run took 09:04–18:38 UTC including fixes.

| stage | recorded time |
|---|---|
| `select`, `asof`, `deploy`, `ranges` | about 30 minutes |
| `controls` | about 1.5 hours |
| `count` | about 1.5 hours |
| `finish` | about 2.5 hours |
| `union` (Celo) | about 30 minutes |
| `replicate` | about 5 hours, mostly Base `NewFeedback` over 7 million blocks |

Base and 0G dominate the run time. A single small chain (`--chains 5000`) takes minutes.

## Files

| path | what |
|---|---|
| `erc8004_usage.py` | the scanner (`selftest`, `select`, `asof`, `deploy`, `ranges`, `controls`, `mergecontrols`, `count`, `finish`, `union`, `replicate`, `report`) |
| `inline/` | four short scripts that were run inline during the measurement, kept verbatim: self-validation, two endpoint-consistency parts, and the Base pre-window count |
| `abis/` | vendored ABIs and `addresses.ts` from the reference implementation, with `PROVENANCE.json` |
| `output/` | the raw record: RPC selection, as-of and deploy blocks, controls, `counts/*.json` (one file per chain, registry and event; validation files include every raw log), replication, self-validation, endpoint consistency, `run.log` and per-stage stdout. Everything from the run except `output/chainlist.json`. |
| `PROVENANCE-chain-list.md` | where the excluded `output/chainlist.json` came from, its SHA-256 and a command to fetch and verify it |
| `ADDENDUM-2026-11-11-*.md`, `addenda/` | three dated addenda, with their code and raw call output |
| `ADDENDUM-D-cb1b-ethereum.md` | addendum D (16 November 2026): validation events at the testnet-listed Validation proxy on Ethereum mainnet; code and raw output in `addenda/2026-11-16_*` |
| `SHA256SUMS` | SHA-256 of every file in this repository except `SHA256SUMS` itself and git metadata (`shasum -a 256 -c SHA256SUMS`) |

`output/rpc_selection.v1.json` is the endpoint selection before `ranges` re-ranked it. It is kept as part of the record.
The run was made in a private working repository. It was copied here without changes to any measured number or raw
output, and with one file left out: `output/chainlist.json`.

## Corrections

None as of first publication (11 November 2026). Later corrections go here with a date and in new files. The original
output is never edited.
- 16 November 2026: [addendum D](ADDENDUM-D-cb1b-ethereum.md) reads the testnet-listed Validation proxy `0x8004Cb1BF31DAf7788923b405b754f57acEB4272` on Ethereum mainnet, which the count did not scan. It found 0 validation events there, so the Ethereum count remains 0.

## Licence

Code: MIT. The upstream files in `abis/` keep their own licence. See [`LICENSE`](LICENSE).
