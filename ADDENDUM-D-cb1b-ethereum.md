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
