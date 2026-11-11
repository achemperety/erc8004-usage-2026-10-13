# Addendum B, 11 November 2026: which Base ValidationRegistry does forum post #437 mean?

This addendum changes no result of the 13 October 2026 measurement.

## The post

Ethereum Magicians, topic 25098 (*ERC-8004: Trustless Agents*), post #437, by `RealSpap`, 2026-11-06T20:35:28Z
(<https://ethereum-magicians.org/t/25098/437>; read from
<https://ethereum-magicians.org/posts/by_number/25098/437.json> on 2026-11-11). The post says that "the third proxy
is the ValidationRegistry at `0x8004Cb1BF31DAf7788923b405b754f57acEB4272`", that it exists on Ethereum and Base only,
and that "on Base it still points at the one it was created with, which has none of the three validation functions
(validationRequest, validationResponse, getValidationStatus)". It suggests reading the EIP-1967 implementation slot with
`cast storage`.

## The three addresses compared

| | address |
|---|---|
| ValidationRegistry named in post #437 | `0x8004Cb1BF31DAf7788923b405b754f57acEB4272` |
| ValidationRegistry the scanner used on every chain (`erc8004_usage.py`, `ADDR["validation"]`, from the reference repo's `scripts/addresses.ts` `MAINNET_ADDRESSES`) | `0x8004Cc8439f36fd5F9F049D9fF86523Df6dAAB58` |
| Emitter of the 15 Base `ValidationRequest` logs (from each transaction's receipt, re-read on 2026-11-11) | `0x8004Cc8439f36fd5F9F049D9fF86523Df6dAAB58`, all 15 |

**They are not the same proxy.** The post refers to `0x8004Cb1B…4272`. The measurement scanned `0x8004Cc84…AB58`, and
all 15 events came from that address. In the reference repo's `scripts/addresses.ts` (vendored here as
`abis/addresses.ts.vendored`), `0x8004Cb1B…4272` is the `validationRegistry` entry of `TESTNET_ADDRESSES`. The
`MAINNET_ADDRESSES` entry is `0x8004Cc84…AB58`.

Because the two differ, the EIP-1967 implementation slot was read for **both** proxies, at the as-of block and today,
so the difference can be seen directly.

## EIP-1967 implementation slot on Base

Slot `0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc`, read with `eth_getStorageAt` on four
public endpoints (`base.gateway.tenderly.co`, `mainnet.base.org`, `base.publicnode.com`, `base.drpc.org`). All four
agreed on every value below.

| proxy | at as-of block 52,546,365 (2026-10-13T09:01:17Z) | at block 56,001,562 (2026-11-11, run time 09:51 UTC) |
|---|---|---|
| `0x8004Cc84…AB58` (scanned) | `0xdb31f5d9167f8ebc8b30fbbf814c4d297c2d7f99` | `0xdb31f5d9167f8ebc8b30fbbf814c4d297c2d7f99` |
| `0x8004Cb1B…4272` (post #437) | `0xd53de688e0b0ad436fbdbda00036832ff6499234` | `0xd53de688e0b0ad436fbdbda00036832ff6499234` |

Both proxies have the same 130-byte runtime code (keccak `0xd0e45b1d…2b41`) at both blocks.

For each implementation's runtime code at both blocks, the check below searched for a `PUSH4 <selector>` of the three
validation functions in the vendored `ValidationRegistry` ABI (`addenda/2026-11-11_selector_check.py`, output in
`addenda/2026-11-11_selector_check.txt`):

| implementation | code size | `validationRequest` `0xaaf400c4` | `validationResponse` `0x3d659a96` | `getValidationStatus` `0xff2febfc` |
|---|---:|---|---|---|
| `0xdb31f5d9…7f99` (behind the scanned proxy) | 5,876 bytes | present | present | present |
| `0xd53de688…9234` (behind the post's proxy) | 2,188 bytes | absent | absent | absent |

## What this establishes

- Post #437 and this measurement are about **different contracts** on Base. The post does not describe the contract
  whose events were counted. Its observation does not change the 15 requests and 12 responses counted on Base.
- At the as-of block and today, the proxy the scanner measured on Base delegates to an implementation that contains the
  dispatch selectors of all three validation functions. The 15 events were emitted by that proxy.
- At the as-of block and today, the proxy the post names delegates to an implementation that contains none of the three
  selectors. This agrees with the post's description for Base, at those two blocks.
- Neither implementation slot changed between 13 October and 11 November 2026.

## What this does not establish

- **History before the as-of block.** `Upgraded(address)` logs were not scanned. "Created with" (the post's phrase) is
  therefore not verified here. Neither is whether `0x8004Cb1B…4272` ever pointed to a different implementation on Base
  or emitted validation events. The 13 October measurement did not scan that address on any chain, so any events it
  emitted are outside this measurement.
- **Ethereum mainnet.** The post's claim that `0x8004Cb1B…4272` "runs a real implementation" on Ethereum was not checked.
- **Owners.** The post's statements about proxy owners were not checked.
- **What the code does.** A `PUSH4 <selector>` search is a heuristic for the function dispatcher. It is not a
  decompilation, and it does not prove what a function does or that a call would succeed.
- **Intent.** Whether the second proxy on Base is meant to remain on its current implementation is a question for the
  registry team. On-chain data cannot answer it.
