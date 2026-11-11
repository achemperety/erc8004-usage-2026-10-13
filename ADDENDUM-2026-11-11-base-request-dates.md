# Addendum A, 11 November 2026: dates of the 15 Base validation requests

This addendum changes no result of the 13 October 2026 measurement. It only adds a calendar date to each of the
15 `ValidationRequest` logs that the measurement found on Base (chainId 8453) up to the as-of block 52,546,365.

## Source and method

- **Input:** `output/counts/8453_validation_ValidationRequest.json` from the original run. This addendum uses the
  block number, log index, transaction hash and topics of each of its 15 logs as they were recorded.
- **Calls (read-only, 2026-11-11 09:51 UTC):** `eth_getBlockByNumber` for each block on two public endpoints,
  `base.gateway.tenderly.co` and `mainnet.base.org`. Both endpoints returned the same timestamp for all 15 blocks.
  `eth_getTransactionReceipt` for each transaction re-read the log at the recorded log index. In all 15 cases it was
  emitted by `0x8004Cc8439f36fd5F9F049D9fF86523Df6dAAB58` with topic0 `0x530436c3…5059` (`ValidationRequest`).
- **Code and raw output:** `addenda/2026-11-11_base_calls.py` and `addenda/2026-11-11_base_calls.json`.
- `agentId` is topic2 and `validator` is topic1 of the log, exactly as recorded.

## The 15 requests

| # | block | log index | timestamp (UTC) | UTC date | agentId | validator | tx |
|---:|---:|---:|---|---|---:|---|---|
| 1 | 43134133 | 169 | 2026-03-09T12:00:13Z | 2026-03-09 | 25331 | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | `0x7f95b566aab2706023804dd63c4cd1075d79817557bb212695f9ee3ae857b2fa` |
| 2 | 43134146 | 869 | 2026-03-09T12:00:39Z | 2026-03-09 | 25331 | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | `0x3fdd4cca086e6cf9db090fb316c73e4b177002aecb8887c02a1f391dfe9d9cc4` |
| 3 | 43134682 | 677 | 2026-03-09T12:18:31Z | 2026-03-09 | 25331 | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | `0x879ab0be74e44a8f0e7eab931b1870dc25bb05403f60573e3dda55fc45181c31` |
| 4 | 43134858 | 543 | 2026-03-09T12:24:23Z | 2026-03-09 | 25331 | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | `0xde34e59888f7067c4d307fa39cb28ff969d0ff5b65caea51255f7449cdfa288e` |
| 5 | 43134870 | 423 | 2026-03-09T12:24:47Z | 2026-03-09 | 25331 | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | `0x2cfe585197abe48d45d3765d03a150f7b32782606b5de621d93e9f1132d90346` |
| 6 | 43135041 | 199 | 2026-03-09T12:30:29Z | 2026-03-09 | 25331 | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | `0xfe736921d8b98c5e7cb776e360984163875fa148047970816eb78f9017cd807b` |
| 7 | 43138402 | 255 | 2026-03-09T14:22:31Z | 2026-03-09 | 25331 | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | `0xc18d0be0454277caa0380e7b94f43fe177e96553b6a5e4947f0368e083b41d42` |
| 8 | 43138830 | 284 | 2026-03-09T14:36:47Z | 2026-03-09 | 25331 | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | `0x3f0150b496c9e1a1743329be66a44ef02279fb3913b6b3d54d8a1280ba9fbd90` |
| 9 | 43140910 | 785 | 2026-03-09T15:46:07Z | 2026-03-09 | 25331 | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | `0x1501c8da7ecbb0f05840ccb458113b81f65c1f4a2410e0a6dd009b2f232bfd81` |
| 10 | 43177272 | 454 | 2026-03-10T11:58:11Z | 2026-03-10 | 25331 | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | `0xc4b96f55d1e494285fa8a5a3990b2b86f81f47b0a7abd1e0e1f0991de8b470d3` |
| 11 | 43181588 | 302 | 2026-03-10T14:22:03Z | 2026-03-10 | 25331 | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | `0x3366fc9f0a948b6e344be1723bf43dcb49e93923f42c0f30ae87ccb8e1f82658` |
| 12 | 43183045 | 508 | 2026-03-10T15:10:37Z | 2026-03-10 | 25331 | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | `0x4f88c401bb0c06eb5f465206c767fd64fd1acdfb842fc3699a02e01c0359f89f` |
| 13 | 50073293 | 532 | 2026-08-17T03:05:33Z | 2026-08-17 | 60102 | `0x3a77efd0f47907a32ee9f5c90d9ec91ba7fca4c3` | `0x8b4bb34b6681dd0406b19a14ad8a939afb4dbeddb0905881f2713b67ed51620c` |
| 14 | 51606429 | 729 | 2026-09-21T14:50:05Z | 2026-09-21 | 95265 | `0x0c3a19bea92480a978f2a358e8e1e87b9dad14b5` | `0xc73eb383890e98b5f19671e54654ba31a5e1b752af5fcde4a7e4e84d3866ec2d` |
| 15 | 51702363 | 653 | 2026-09-23T20:07:53Z | 2026-09-23 | 95374 | `0x6328f2fe483922721d94b33ee99e9938da3b7911` | `0x885769e81d7fb3218cf0e0659e57f1bac48469aabf950222023b14ecb47e7235` |

## Count by month (UTC)

| month | requests |
|---|---:|
| 2026-03 | 12 |
| 2026-04 | 0 |
| 2026-05 | 0 |
| 2026-06 | 0 |
| 2026-07 | 0 |
| 2026-08 | 1 |
| 2026-09 | 2 |
| 2026-10 (to the as-of block, 09:01:17 UTC on 13 October) | 0 |

Base's Validation registry was deployed at block 41,663,785, so the months before March 2026 had no request either.

## What this adds

- Twelve of the 15 requests came from one agent, 25331, to one validator, over about 27 hours on 9–10 March 2026.
- The other three are one each from three different agents: 17 August, 21 September and 23 September 2026.
- All 12 March requests fall inside Marsel Sultanov's final Base window (blocks 42,003,733–49,019,181), which matches
  his "12 requests". The three later requests are all after his last indexed block.
- This addendum does not date the 12 `ValidationResponse` logs.
