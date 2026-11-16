# Addendum D, 16 November 2026: validation events at the testnet-listed Validation proxy on Ethereum mainnet

This addendum changes no file of the 13 October 2026 measurement and no earlier addendum. It reads one address on one
chain that the 13 October count did not read. **Result: the Ethereum count remains 0.**

## What was missed, and why

The 13 October scan read `ValidationRequest` and `ValidationResponse` on every chain at one address only,
`0x8004Cc8439f36fd5F9F049D9fF86523Df6dAAB58`. That is `ADDR["validation"]` in `erc8004_usage.py`, taken from the
`MAINNET_ADDRESSES` entry of the reference repo's `scripts/addresses.ts`. On Ethereum it scanned from that proxy's
deploy block 24,339,874 to the as-of block 26,182,323 (`output/counts/1_validation_ValidationRequest.json`,
`output/as_of.json`).

The `TESTNET_ADDRESSES` entry of the same file, `0x8004Cb1BF31DAf7788923b405b754f57acEB4272`
(`abis/addresses.ts.vendored`, line 70), also has proxy code on Ethereum mainnet. RealSpap reported this on Ethereum
Magicians, topic 25098. The posts are [#445](https://ethereum-magicians.org/t/25098/445) (2026-11-12),
[#447](https://ethereum-magicians.org/t/25098/447) (2026-11-15T16:07Z) and
[#449](https://ethereum-magicians.org/t/25098/449) (2026-11-15T20:30Z). His errata `errata/E-2026-11-12-erc8004-validation-registry.md` in
`github.com/RealSpap/authority-risk-oracle-showcase` (revised 2026-11-15) gives the address history. Before
24,339,874, that proxy pointed to an implementation with the validation functions. Any validation events it emitted
would therefore be outside the 13 October count. Addendum B checked this address on Base only and listed
Ethereum as not checked. The README's *Limits* section names it as invisible to the measurement.

**Credit:** the address history of `0x8004Cb1B…4272` on Ethereum, meaning the creation block, the three upgrades and
the implementation with the validation functions, is RealSpap's finding. This addendum re-derives each of his figures
independently and says whether it matches.

## Method

- **Code:** `addenda/2026-11-16_cb1b_ethereum.py`. Raw output: `addenda/2026-11-16_cb1b_ethereum.json`.
- **Reused from the 13 October scanner** (`erc8004_usage.py`, imported unchanged):
  - `event_sig`, which derives the topics from the vendored ABI `abis/ValidationRegistry.json`. `ValidationRequest`
    and `ValidationResponse` are the two topics pinned in `selftest`. `Upgraded(address)` comes from the same ABI.
  - `corrupt` and `has_code`.
  - The log reader `scan_parallel`/`scan`, with its existing rules: split a range on error or at a cap, never treat
    an error as zero, re-check every log, de-duplicate.
  - The chunk sizes of the Ethereum count: initial 10,000 blocks, maximum 500,000. A node that refuses a range makes
    the reader split it.
- **Two nodes, no failover:** `https://mainnet.gateway.tenderly.co` and `https://rpc.mevblocker.io/fast`. Each node is
  a separate client with one URL, so every figure below is per node. Both endpoints served the 13 October Ethereum
  run (`output/rpc_selection.json`). They are run by different operators. Whether their back ends are independent
  cannot be seen from outside. Other keyless endpoints refused `eth_getLogs` (HTTP 400, 403, 429, 503) or did not resolve
  (`eth.drpc.org`, `eth-mainnet.public.blastapi.io`, `ethereum.publicnode.com`, `eth.api.onfinality.io/public`,
  `ethereum.blockpi.network`, `eth.merkle.io`, `eth.llamarpc.com`). `1rpc.io/eth` limits `eth_getLogs` to 50 blocks.
- **Blocks:**
  - Snapshot block of the 13 October count: 26,182,323.
  - Current head fixed for this run: 26,423,018, which is the lower of the two nodes' heads (26,423,274) minus 256,
    2026-11-15T21:12:11Z.
  - Run: 2026-11-15T22:04:00Z to 22:23:10Z.
- **Read-only:** `eth_chainId`, `eth_blockNumber`, `eth_getBlockByNumber`, `eth_getCode`, `eth_getStorageAt`,
  `eth_getLogs`, `eth_getTransactionByHash`, `eth_call`. The last two would only be used if validation events were
  found, and none were.
- **Run 1, kept as `addenda/2026-11-16_cb1b_ethereum.run1.json`:**
  - The first run, 21:57–22:03Z with head 26,422,987, completed on Tenderly. Apart from the head block, its results
    are identical to those below.
  - On MEV Blocker it stopped at one point read that timed out. The scanner's client does not retry timeouts, because
    it relies on the log reader to split a slow range.
  - The script was then given a retry of up to five attempts for point reads only. `eth_getLogs` behaves exactly as
    before. Both nodes were run again, and the figures below are from that second run.

## 1. Address history: expected (RealSpap) vs found

| item | RealSpap | Tenderly | MEV Blocker | |
|---|---|---|---|---|
| creation block, by binary search on `eth_getCode` | 24,204,475 | 24,204,475 | 24,204,475 | **matches** |
| code one block earlier (24,204,474) | — | none | none | — |
| proxy runtime code | — | 130 bytes, keccak `0xd0e45b1d…2b41` | same | — |
| `Upgraded` events, creation to snapshot | 3 | 3 | 3 | **matches** |
| `Upgraded` events, creation to head 26,423,018 | — | 3 (no later upgrade) | 3 | — |
| 1st `Upgraded` | block 24,204,475 | 24,204,475 → `0xd53de688…9234` | same | **matches** |
| 2nd `Upgraded` (switch to an implementation with all three selectors) | block 24,204,487, 2026-01-10 13:06:11 UTC, → `0x106e3d85…2b0e` | 24,204,487, 2026-01-10T13:06:11Z → `0x106e3d85…2b0e` | same | **matches** |
| 3rd `Upgraded` | block 24,339,656 → `0xdb31f5d9…7f99` | 24,339,656, 2026-01-29T09:37:11Z → `0xdb31f5d9…7f99` | same | **matches** |
| EIP-1967 slot at creation block 24,204,475 | `0xd53de688…9234` | `0xd53de688…9234` | same | **matches** |
| slot at 24,204,486 / 24,204,487 | — | `0xd53de688…9234` / `0x106e3d85…2b0e` | same | — |
| slot at snapshot 26,182,323 and at head 26,423,018 | `0xdb31f5d9…7f99` | `0xdb31f5d9…7f99` | same | **matches** |

For each `Upgraded` log after the creation block, the slot one block earlier holds the previous implementation, and
the slot at the log's block holds the implementation named in the log. At the creation block, the slot equals the
first log's implementation.

| `Upgraded` | block | UTC | tx | log index | implementation |
|---:|---:|---|---|---:|---|
| 1 | 24204475 | 2026-01-10T13:03:47Z | `0x5a22b472636ee0330e91138978c3167939a8a44167c086a2ba8c8022f9b34868` | 428 | `0xd53de688e0b0ad436fbdbda00036832ff6499234` |
| 2 | 24204487 | 2026-01-10T13:06:11Z | `0xe8f4f82c5ffa7bba1045a001f1f0417d9f94c7afe93c4a8930eccea7cb67293b` | 727 | `0x106e3d8500b92a86d669702e75097e945c2e2b0e` |
| 3 | 24339656 | 2026-01-29T09:37:11Z | `0x08f38f7a65f755f904d8e227c953a6b4c792a21e154c0d0f9721b8b051f0e099` | 889 | `0xdb31f5d9167f8ebc8b30fbbf814c4d297c2d7f99` |

## 2. Selectors in each implementation

The check is the same as in addendum B: a `PUSH4 <selector>` search in the runtime code for the three validation
functions of the vendored ABI. The code was read at the implementation's first `Upgraded` block and at the head. The
results were identical on both nodes and at both blocks.

| implementation | active at Cb1B | code size | keccak | `validationRequest` `0xaaf400c4` | `validationResponse` `0x3d659a96` | `getValidationStatus` `0xff2febfc` | RealSpap |
|---|---|---:|---|---|---|---|---|
| `0xd53de688…9234` | 24,204,475–24,204,486 | 2,188 | `0x2af9793a…91b4` | absent | absent | absent | none of the three, 2,188 bytes: **matches** |
| `0x106e3d85…2b0e` | 24,204,487–24,339,655 | 6,044 | `0x0235d32a…d792` | present | present | present | all three, 6,044 bytes: **matches** |
| `0xdb31f5d9…7f99` | 24,339,656 to head | 5,876 | `0x14ffccec…303c6` | present | present | present | all three: **matches** |

`0xd53de688…9234` has the same code size and keccak as the implementation behind this address on Base in
addendum B. `0xdb31f5d9…7f99` is the implementation behind the scanned proxy `0x8004Cc84…AB58` on Base in addendum B.

## 3. Counts at `0x8004Cb1B…4272` on Ethereum, from the creation block

| range | Tenderly: requests / responses | MEV Blocker: requests / responses |
|---|---:|---:|
| (a) 24,204,475 – 26,182,323 (snapshot of the 13 October count) | **0 / 0** | **0 / 0** |
| (b) 24,204,475 – 26,423,018 (head of this run) | **0 / 0** | **0 / 0** |
| inside 24,204,475 – 24,204,486 (implementation without the functions; 0 expected by construction) | 0 / 0 | 0 / 0 |

Scan statistics:
- Tenderly: 36 calls for each full range, no splits.
- MEV Blocker: 199 calls with 12 splits for (a), and 157 calls with 20 splits for (b).
- Duplicates dropped: 0.

The two nodes read the same ranges with very different chunking and returned the same result.

## 4. Controls

These follow the design of the 13 October count. All controls passed on both nodes.

| control | range | expected | Tenderly | MEV Blocker |
|---|---|---|---:|---:|
| (a) pre-deployment, both validation topics | 24,004,475 – 24,204,474 (200,000 blocks ending at creation − 1) | 0 | 0 | 0 |
| (b) corrupted topic0, `…5059` → `…5050` and `…49ae` → `…49a0` | 24,204,475 – 26,423,018 (full range) | 0 | 0 | 0 |
| (b′) true topic0, same range | 24,204,475 – 26,423,018 | — | 0 | 0 |
| (c) positive: `Upgraded` logs at this address, same reader, same chunking | 24,204,475 – 26,423,018 | ≥ 1, each matching a slot change | 3, all matching | 3, all matching |

Points to weigh:

- **(b′) is 0.** As on the original Ethereum validation row, (b) therefore only shows that an empty range stayed empty.
- **Control (c) shows the reader returns events at this address with these chunk sizes.** Its three logs are confirmed
  independently by storage reads at each block.
- **All three `Upgraded` logs are in the first 135,000 blocks of a 2.2-million-block range.** Control (c) does not show
  that the reader returns logs late in the range. The agreement of two nodes with different chunking is the only
  cross-check there.

## 5. Validation events in detail

None. With no request, there is nothing for step 8 (validator, requester, owner at the request block, as in
addendum C). The script implements that step but did not run it.

## Effect on the published totals

**The Ethereum count remains 0.** No `ValidationRequest` or `ValidationResponse` was emitted at
`0x8004Cb1BF31DAf7788923b405b754f57acEB4272` on Ethereum mainnet:
- from its creation block 24,204,475 to the 13 October snapshot block 26,182,323;
- nor up to block 26,423,018.

## RealSpap's other networks

His errata covers further networks. Those figures are his work and are cited, not reproduced, here. One example was
replayed:

- **Arbitrum One, reproduced by us.** We read `Upgraded(address)` logs at `0x8004Cc8439f36fd5F9F049D9fF86523Df6dAAB58`,
  blocks 428,895,484–428,895,794, on `https://arb1.arbitrum.io/rpc` with the scanner's reader. Expected 2, found 2:
  **matches**.
  - Block 428,895,484 (2026-02-05T13:16:11Z) → `0xcb7af40c0be4fb92e183942b6dbb6b14a888f067`.
  - Block 428,895,794 (13:17:28Z) → `0xdb31f5d9167f8ebc8b30fbbf814c4d297c2d7f99`.
  - Both values agree with his errata.
  - The endpoint has no historical state ("missing trie node"), so the implementation slot was not read there.
  - Code: `addenda/2026-11-16_arbitrum_upgraded.py`. Output: `addenda/2026-11-16_arbitrum_upgraded.json`.
- **Every other network in his errata:** not replayed.

## What this does not establish

- **Other addresses.** Only the testnet entry `0x8004Cb1B…4272` on Ethereum was added. Other chains are not covered,
  and neither are other addresses.
- **What the code does.** As in addendum B, a `PUSH4` search finds dispatcher entries. It does not prove what a
  function does, or that a call would have succeeded.
- **Unemitted activity.** Calls that reverted, or state written without an event, are not visible in logs.

## Update, 2026-11-16: all-topics read (RealSpap's check, replayed)

This section adds to addendum D. It changes no line above it, no earlier file and no published total.

RealSpap read every log at `0x8004Cb1B…4272` on Ethereum mainnet with no topic filter, over blocks 24,204,475 to
26,427,741 ([#451](https://ethereum-magicians.org/t/25098/451), 2026-11-16T13:27Z). His figures: 7 logs, made up of
3 `Upgraded`, 2 `OwnershipTransferred` and 2 `Initialized`, and no validation events. This update repeats that read.

**Method**

- **Code:** `addenda/2026-11-16_cb1b_all_topics.py`. Raw output: `addenda/2026-11-16_cb1b_all_topics.json`.
- **Range:** his range, 24,204,475 – 26,427,741 (2,223,267 blocks). Both nodes' heads at the run were 26,428,030,
  so the range ends at least 256 blocks below the head.
- **Nodes:** the two nodes of addendum D, `https://mainnet.gateway.tenderly.co` and `https://rpc.mevblocker.io/fast`,
  each a separate client with no failover.
- **Run:** 2026-11-16T13:56:31Z to 14:01:16Z.
- **Read-only:** `eth_chainId`, `eth_blockNumber`, `eth_getBlockByNumber`, `eth_getLogs`.
- **Chunk sizes:** those of addendum D, initial 10,000 blocks and maximum 500,000, with 6 parallel segments.
- **Reader:** the scanner's reader `scan` always sends a topic0 filter. It also rejects any returned log whose topic0
  was not requested. So it cannot read all topics unchanged, and `erc8004_usage.py` was not edited.
  - The script takes the source of `scan` and `scan_parallel` and applies the substitutions listed in the script and
    in the output. Each substitution must match exactly once. They remove the `topics` key from the `eth_getLogs`
    request and the topic0 re-check, and let a log with no topics be counted.
  - The derived reader runs in the scanner's own module namespace.
  - Everything else is the scanner's code as it is: split on error, split at a suspected cap, adaptive chunk size,
    re-check of block range and address, and de-duplication.
  - The output records the SHA-256 of `erc8004_usage.py` (`f55fd146…49a5ce`, the value in `SHA256SUMS`) and of the
    derived source.
- **Cross-check:** on each node, the topic0 values found were read again with the unchanged filtered reader
  (`scan_parallel`, OR-filter on those topic0 values, same range and chunk sizes). This is a check of the derived
  reader against the original one on the same node. It is not an independent source.

**Topic0 identification**

| event | topic0 | source | found |
|---|---|---|---:|
| `Upgraded(address)` | `0xbc7cd75a…2d3b` | vendored ABI | 3 |
| `ValidationRequest(address,uint256,string,bytes32)` | `0x530436c3…5059` | vendored ABI | 0 |
| `ValidationResponse(address,uint256,bytes32,uint8,string,bytes32,string)` | `0xafddf629…49ae` | vendored ABI | 0 |
| `OwnershipTransferred(address,address)` | `0x8be0079c…57e0` | computed | 2 |
| `Initialized(uint8)` | `0x7f26b83f…2498` | computed | 0 |
| `Initialized(uint64)` | `0xc7f505b2…81d2` | computed | 2 |

Both `Initialized` logs match **`Initialized(uint64)`**. This is also the `Initialized` signature in the vendored ABI.
No log has a topic0 outside this table, and no log has zero topics.

**Logs found, identical on both nodes**

| # | block | UTC | tx | log index | event |
|---:|---:|---|---|---:|---|
| 1 | 24204475 | 2026-01-10T13:03:47Z | `0x5a22b472636ee0330e91138978c3167939a8a44167c086a2ba8c8022f9b34868` | 428 | `Upgraded` |
| 2 | 24204475 | 2026-01-10T13:03:47Z | `0x5a22b472636ee0330e91138978c3167939a8a44167c086a2ba8c8022f9b34868` | 429 | `OwnershipTransferred` |
| 3 | 24204475 | 2026-01-10T13:03:47Z | `0x5a22b472636ee0330e91138978c3167939a8a44167c086a2ba8c8022f9b34868` | 430 | `Initialized(uint64)` |
| 4 | 24204487 | 2026-01-10T13:06:11Z | `0xe8f4f82c5ffa7bba1045a001f1f0417d9f94c7afe93c4a8930eccea7cb67293b` | 727 | `Upgraded` |
| 5 | 24204487 | 2026-01-10T13:06:11Z | `0xe8f4f82c5ffa7bba1045a001f1f0417d9f94c7afe93c4a8930eccea7cb67293b` | 728 | `OwnershipTransferred` |
| 6 | 24204487 | 2026-01-10T13:06:11Z | `0xe8f4f82c5ffa7bba1045a001f1f0417d9f94c7afe93c4a8930eccea7cb67293b` | 729 | `Initialized(uint64)` |
| 7 | 24339656 | 2026-01-29T09:37:11Z | `0x08f38f7a65f755f904d8e227c953a6b4c792a21e154c0d0f9721b8b051f0e099` | 889 | `Upgraded` |

The three `Upgraded` logs are the same (block, log index, tx) as in section 1 of this addendum.

| | Tenderly | MEV Blocker |
|---|---:|---:|
| logs, all topics | 7 | 7 |
| calls / splits, all-topics read | 36 / 0 | 200 / 21 |
| duplicates dropped | 0 | 0 |
| filtered cross-check: same 7 logs | yes (36 calls, 0 splits) | yes (226 calls, 16 splits) |

**Result**

- **Matches RealSpap:** 7 logs, of which 3 are `Upgraded`, 2 `OwnershipTransferred` and 2 `Initialized`, on both
  nodes.
- **Validation events: 0** (`ValidationRequest` 0, `ValidationResponse` 0), as expected. This agrees with section 3.
  **The Ethereum count remains 0.**
- **Last log:** block 24,339,656, which is 135,181 blocks into a range of 2,223,267 blocks, so at **0.061** of the
  range. Everything after the first 6.1 % of the range returned no log on either node.
- **What this read shows about late-range coverage: nothing.** No log of any kind lies in the last 93.9 % of the
  range. That fits a proxy that emitted nothing after its last upgrade. It would also fit a reader or node that missed
  late logs. Without a known log late in the range, this read cannot tell the two apart. The limit stated in
  section 4 still applies. The agreement of two nodes, with different chunking (36 calls against 200 calls with 21
  splits), remains the only cross-check there.

## Update, 2026-11-16: late-range positive control

This section adds to addendum D. It changes no line above it, no earlier file and no published total.

Caveat 2 of this addendum: no check showed that the reader returns logs late in the range. Every log found at
`0x8004Cb1B…4272` is in the first 6.1 % of it. RealSpap suggested the remedy
([#453](https://ethereum-magicians.org/t/25098/453)). Run the same reader, with the same chunking, the same range and
the same two nodes, on a contract known to emit logs late in the range, and confirm that logs come back from the last
part. **Credit:** the design of this control is RealSpap's.

**Method**

- **Code:** `addenda/2026-11-16_late_range_control.py`. Raw output: `addenda/2026-11-16_late_range_control.json`.
- **Reader:** the scanner's filtered `scan_parallel`, unchanged and imported from `erc8004_usage.py` (SHA-256
  `f55fd146…49a5ce`, as in `SHA256SUMS`). It filters on topic0, splits on error or at a suspected cap, re-checks
  every log and de-duplicates.
- **Chunk sizes:** those of addendum D, initial 10,000 blocks and maximum 500,000, with 6 parallel segments.
- **Range:** the all-topics range of the previous update, 24,204,475 – 26,427,741 (2,223,267 blocks). Both nodes'
  heads at the run were 26,429,029.
- **Nodes:** `https://mainnet.gateway.tenderly.co` and `https://rpc.mevblocker.io/fast`, each a separate client with
  one URL and no failover.
- **Run:** 2026-11-16T17:17:35Z to 17:24:50Z.
- **Read-only:** `eth_chainId`, `eth_blockNumber`, `eth_getBlockByNumber`, `eth_getCode`, `eth_getLogs`.
- **Stored output:** the JSON keeps per-node counts, deciles, the last five logs, and a SHA-256 of each node's sorted
  (block, tx, log index) list. It does not keep the 94,018 logs themselves.

**Target and why**

Option (a) of the instructions was used: the ERC-8004 registries on Ethereum mainnet, at the addresses and topic0s of
the 13 October scan (`ADDR` and `event_sig` in `erc8004_usage.py`, from the vendored ABIs).

| event | address | topic0 |
|---|---|---|
| IdentityRegistry `Registered(uint256,string,address)` | `0x8004A169FB4a3325136EB29fA0ceB6D2e539a432` | `0xca52e62c…bc4a` |
| ReputationRegistry `NewFeedback(…)` | `0x8004BAa17C55a88189AE136b182e5fdA19dE9b63` | `0x6a4a6174…febc` |

- **Why these:** both emit logs in the last 10 % of the range, so the ERC-20 fallback (b) was not needed.
- **A comparison point:** they have a published count up to the 13 October snapshot block, so a second test is
  possible.
- **Same scope as the original question:** they are the scanner's own targets on the same chain.

**Results, per node**

| | Tenderly: `Registered` | MEV Blocker: `Registered` | Tenderly: `NewFeedback` | MEV Blocker: `NewFeedback` |
|---|---:|---:|---:|---:|
| logs, full range | 56,568 | 56,568 | 37,450 | 37,450 |
| logs in the last 10 % (block > 26,205,415) | 2,406 | 2,406 | 7,404 | 7,404 |
| last log block | 26,427,688 | 26,427,688 | 26,427,708 | 26,427,708 |
| last log as fraction of range | 0.999976 | 0.999976 | 0.999985 | 0.999985 |
| `eth_getLogs` calls / splits | 94 / 3 | 243 / 14 | 42 / 0 | 221 / 12 |
| largest range returned in one call | 160,000 | 20,000 | 160,000 | 20,000 |
| RPC requests in total, including point reads and refused calls | 100 | 260 | 45 | 236 |
| duplicates dropped | 0 | 0 | 0 | 0 |

The last logs in detail:

- **`Registered`:** block 26,427,688, 2026-11-16T12:47:47Z, tx
  `0xa504c04ff0b2aa2c366b606193f4716b42580da2e78e5070447d5aa43c75f8e2`, log index 292. This is 53 blocks before the
  end of the range.
- **`NewFeedback`:** block 26,427,708, 2026-11-16T12:51:47Z, tx
  `0x40c14a7bb061bbf95c3ceb23c75aec6da287be20c9f76d082ea2e65c7d43586e`, log index 552. This is 33 blocks before the
  end of the range.

**Agreement between nodes**

- **`Registered`:** the (block, tx, log index) sets are identical. 0 logs are found on one node only. The SHA-256 of
  the sorted list is `4f7a1a50…d43c2` on both nodes.
- **`NewFeedback`:** the sets are identical. 0 logs are found on one node only. The SHA-256 is `726c4936…a0be5` on
  both nodes.
- **Chunking:** the two nodes read the range with very different chunking, as in the earlier sections. Tenderly used
  ranges of up to 160,000 blocks. MEV Blocker used ranges of up to 20,000 blocks, with 12–14 splits.

**Distribution over the range, in deciles (identical on both nodes)**

| decile | blocks | `Registered` | `NewFeedback` |
|---:|---|---:|---:|
| 1 | 24,204,475 – 24,426,800 | 23,977 | 1,079 |
| 2 | 24,426,801 – 24,649,127 | 4,548 | 1,711 |
| 3 | 24,649,128 – 24,871,454 | 3,369 | 149 |
| 4 | 24,871,455 – 25,093,780 | 452 | 122 |
| 5 | 25,093,781 – 25,316,107 | 2,292 | 119 |
| 6 | 25,316,108 – 25,538,434 | 1,952 | 7 |
| 7 | 25,538,435 – 25,760,760 | 13,423 | 28 |
| 8 | 25,760,761 – 25,983,087 | 793 | 230 |
| 9 | 25,983,088 – 26,205,414 | 3,356 | 26,601 |
| 10 | 26,205,415 – 26,427,741 | 2,406 | 7,404 |

Every decile returned logs for both events, on both nodes. The registries' deploy blocks, 24,339,871 and 24,339,873,
fall in decile 1.

**Comparison with the published 13 October count**

| | `Registered` | `NewFeedback` |
|---|---:|---:|
| published Ethereum count (`output/counts/1_identity_Registered.json`, `1_reputation_NewFeedback.json`) | 53,903 | 21,337 |
| published scan range | 24,339,871 – 26,182,323 | 24,339,873 – 26,182,323 |
| this read, 24,204,475 – 26,182,323, both nodes | **53,903** | **21,337** |
| of which before the deploy block (24,204,475 – deploy − 1), both nodes | 0 | 0 |
| first log, this read and published | 24,339,925 / 24,339,925 | 24,341,987 / 24,341,987 |

- **Equal on both nodes.** The two counts match the published counts exactly.
- **The start blocks differ, but the comparison is still exact.** The published files hold totals only, not
  individual logs, so the restriction could not be computed from published logs. The published scans started at the
  registries' deploy blocks, not at 24,204,475. This does not change the comparison, for two reasons:
  - Both nodes return no code at deploy − 1 for either registry (`eth_getCode`).
  - This read counts 0 logs between 24,204,475 and deploy − 1.
  So restricting this read to the published start block changes neither count.
- **Not an independent replication.** The 13 October scan was served entirely by Tenderly
  (`rpc_endpoints_used`). The Tenderly part of this match is therefore the same node a month later. The MEV Blocker
  match is the cross-node part.
- **Logs after the snapshot:** 2,665 `Registered` and 16,113 `NewFeedback`, on both nodes. These are not part of
  any published total.

**Widest ranges at Cb1B, and a fixed-chunk re-read**

The reader is adaptive. At the quiet Cb1B address it may have read wider ranges than this control did. Some nodes
answer a range that is too wide with an empty result instead of an error. The widest range returned successfully by
one `eth_getLogs` call at Cb1B:

| | Tenderly | MEV Blocker |
|---|---:|---:|
| section 3 of this addendum (validation scan) | not recorded | not recorded |
| all-topics update | 160,000 | 80,000 |
| this control, for comparison | 160,000 | 20,000 |

`addenda/2026-11-16_cb1b_ethereum.json` records chunks and splits, but not the widest range. MEV Blocker's 80,000 is
wider than this control's 20,000, and section 3 is not recorded on either node. So the last 10 % of the range was
read again:

- **Range:** 26,205,415 – 26,427,741, which is 222,327 blocks.
- **Chunks:** on both nodes, a fixed chunk of 500,000 blocks, so one call. On MEV Blocker also 80,000 blocks, so
  three calls.
- **No splitting or growth:** each call either returned logs, which were re-checked as the reader does, or its error
  was recorded.
- **Cross-check:** each successful call was compared with Tenderly's 500,000-block read of the same sub-range.
- **Code:** `addenda/2026-11-16_late_range_fixed_chunk.py`.
- **Output:** `addenda/2026-11-16_late_range_fixed_chunk.json` holds run 2, 17:30:07Z–17:31:41Z.
  `addenda/2026-11-16_late_range_fixed_chunk.run1.json` holds run 1, 17:29:04Z–17:29:40Z, made before the
  per-call cross-check was added.

| run 2 | `Registered` (control: 2,406) | `NewFeedback` (control: 7,404) |
|---|---|---|
| Tenderly, chunk 500,000 | 2,406, **match** | 7,404, **match** |
| MEV Blocker, chunk 500,000 | no result: error "service temporarily unavailable" | 7,404, **match**, identical to Tenderly |
| MEV Blocker, chunk 80,000 | 2 of 3 calls returned 1,294 + 769 logs, each identical to Tenderly's sub-range; the 3rd timed out after 30 s | 1 of 3 calls returned 1,592 logs, identical to Tenderly's sub-range; 2 errors |

- **Run 1, Tenderly:** the same as run 2.
- **Run 1, MEV Blocker:** at the 500,000 chunk, both events returned an error. At the 80,000 chunk, one call per
  event succeeded, with 1,294 and 1,592 logs, the same counts as in run 2. The other calls returned errors.
- **Tenderly:** both counts match the control at a fixed chunk of 500,000 blocks. That is wider than any range it used
  at Cb1B. The last logs are identical to the control's.
- **MEV Blocker, calls that returned:** every one returned exactly Tenderly's logs for the same sub-range. This
  includes one call over all 222,327 blocks (`NewFeedback`).
- **MEV Blocker, calls that failed:** each failed with an explicit error or a timeout. None returned an empty or
  short result. The reader splits a range on such an error.
- **MEV Blocker, what is missing:** in neither run did the fixed-chunk re-read of `Registered` complete. So the match
  this check requires is shown on MEV Blocker for `NewFeedback` only.

**Result**

The original pass criteria are met on both nodes, for both events:
- logs in the last 10 % of the range;
- identical (block, tx, log index) sets, with 0 duplicates;
- counts equal to the published counts up to the 13 October snapshot block.

**Caveat 2 is closed for Tenderly. It is not closed for MEV Blocker.**
- **Tenderly:** the reader returned logs from every decile up to 33 blocks before the end of the range, and a fixed
  500,000-block read of the last 10 % matched for both events. So on Tenderly the absence of any log at
  `0x8004Cb1B…4272` after block 24,339,656 is not explained by the reader failing to cover the late part of the range.
- **MEV Blocker:** every wide-range failure seen was an error, not an empty result. But the fixed-chunk re-read of
  `Registered` did not complete, so on this node the caveat stays open.
