# Provenance of `output/chainlist.json`

**This file is not included in this repository.** The 13 October run used it, and it is pinned below to an exact
upstream version that anyone can fetch and verify. It is not republished here because the upstream list contains
third-party RPC URLs with embedded credentials (`user:pass@`, chainIds 8098 and 67390) and 13 ENS registry addresses,
none of them used by this measurement. To recreate it at the path the scanner expects, run this from the repository
root:

```sh
curl -sSL -o output/chainlist.json \
  https://raw.githubusercontent.com/ethereum-lists/chains/19d351e845025677a64f603f53d42e86dac5101f/chains.json
echo "0fc1a7f1e164747f15e480efb88f940e4fc24e235b84e1a4cc9c31b029755b5e  output/chainlist.json" | shasum -a 256 -c -
# expect: output/chainlist.json: OK
```

`output/chainlist.json` is listed in `.gitignore`, so a fetched copy is not committed by accident.

`output/chainlist.json` was a copy of the public chain list from chainid.network. The scanner reads it in two places:

- `select` and `ranges` read each chain's public RPC URLs from it. Candidates are the `https://` URLs without a `${…}`
  placeholder or `API_KEY` in them, tried after the hand-picked `EXTRA_RPCS`.
- When the measurement was prepared, it was used by hand to resolve the chain IDs of four chains that the reference
  repo's README lists but `addresses.ts` does not: Robinhood Chain 4663, Billions 45056, Injective 1776 and 0G 16661.

The scanner does not embed the list in its code. `select` downloads it once, to `output/chainlist.json`, if that file
is missing (`erc8004_usage.py`, `cmd_select`), and reuses the file after that. `ranges` reads it without that
fallback, so it fails if the file is absent. The file was 1,194,850 bytes. It is not
the scanner's own source, which is 57,981 bytes.

## Facts

| | value | evidence |
|---|---|---|
| Source URL | `https://chainid.network/chains.json` | Hard-coded in `cmd_select`. The structure matches `chains.json`, not `chains_mini.json`: 2,808 entries with the same 18 fields (`chain, chainId, ens, explorers, faucets, features, icon, infoURL, name, nativeCurrency, networkId, parent, redFlags, rpc, shortName, slip44, status, title`), the same key order and the same minified serialisation as `chains.json` today. `chains_mini.json` has 8 fields. |
| SHA-256 | `0fc1a7f1e164747f15e480efb88f940e4fc24e235b84e1a4cc9c31b029755b5e` | `shasum -a 256` |
| Git blob hash | `8073f0d9a05bd06f4705579d8177f1994a2ba016` | `git hash-object` |
| Exact upstream version | `chains.json` at commit `19d351e845025677a64f603f53d42e86dac5101f` of the `gh-pages` branch of `github.com/ethereum-lists/chains`, which serves chainid.network | The blob hash above equals that commit's `chains.json` blob. None of the 24 other `gh-pages` commits that changed `chains.json` between 2026-10-08 and 2026-10-16 has this blob. |
| Upstream deploy time | 2026-10-13T05:40:55Z | Committer date of `19d351e8`. Message: "Deploying to gh-pages from @ ethereum-lists/chains@35774d63a52ab68ab4007f133056a6db1d0a3c8a 🚀". |
| Upstream source commit | `35774d63a52ab68ab4007f133056a6db1d0a3c8a` on `master`, 2026-10-13T05:31:22Z | Message: "Add BlockVectra public RPC to Robinhood Chain and Robinhood Chain Testnet (#8803)". |
| Validity window upstream | 2026-10-13T05:40:55Z to 2026-10-13T22:44:21Z | The next `gh-pages` commit that changed `chains.json`, `eedfed4e…`, is dated 22:44:21Z. |
| When it was fetched | 2026-10-13, about 09:04 UTC | The file's modification time is 2026-10-13T09:04:15Z. The first `select` line in `output/run.log` is at 09:06:56Z. A working copy of the same size existed in the run's scratch directory at 09:01Z. Each of these times falls inside the upstream validity window. The blob-hash match identifies the content regardless of the exact fetch time. |
| Date inside the file | none | `chains.json` has no generation timestamp or version field. |
| First commit that added it to the measurement record | `61a07cd`, 2026-10-13T23:57:46+05:00 (18:57:46 UTC), "measurements: ERC-8004 validation-layer usage counted from chain logs, 2026-10-13" | History of the private working repository where the run was made. That history is not published, so in this repository the commit hash is a reference only. |
| Licence of the upstream dataset | MIT | `LICENSE` at the root of `github.com/ethereum-lists/chains`, read 2026-11-11, "MIT License / Copyright (c) 2026". The GitHub API also reports the repository licence as MIT. Because the file is not redistributed here, no upstream licence notice is needed. `LICENSE` names the source. |

The fetch-and-check command at the top of this file retrieves exactly this version. It was run on 2026-11-11 and
returned the SHA-256 above.

## Does the list differ today for the chains the measurement uses?

Compared with `https://chainid.network/chains.json` fetched on 2026-11-11 at 09:40 UTC (`Last-Modified: Wed, 11 Nov 2026
06:03:57 GMT`, SHA-256 `f0786851ff11ff0664ede064650d8c65feddf04356103466c821e041f4fdb5ad`, 2,858 entries):

- **Chain IDs and names: no differences.** All 27 chain IDs in the scanner's `CHAINS` table are present in both
  versions, with the same `name` and `shortName`. That includes the 21 measured chains and the six unmeasured ones.
  `status` and `redFlags` are also unchanged.
- **RPC lists: changed for 9 of the 21 measured chains**, and for BSC, which was not measured:

| chainId | chain | added to `rpc` since the snapshot | removed |
|---:|---|---|---|
| 1 | Ethereum | `rpc.swiftnodes.io/…?key=${SWIFTNODES_API_KEY}`, `api.blockvectra.com/v1/eth_mainnet/public` | — |
| 10 | Optimism | `rpc.swiftnodes.io/…?key=${SWIFTNODES_API_KEY}` | — |
| 100 | Gnosis | `rpc.swiftnodes.io/…?key=${SWIFTNODES_API_KEY}` | — |
| 137 | Polygon | `rpc.swiftnodes.io/…?key=${SWIFTNODES_API_KEY}`, `api.blockvectra.com/v1/polygon_mainnet/public` | — |
| 1088 | Metis | `rpc.swiftnodes.io/…?key=${SWIFTNODES_API_KEY}` | — |
| 4663 | Robinhood Chain | `robinhood.daybreak-rpc.network`, `rpc.swiftnodes.io/…?key=${SWIFTNODES_API_KEY}` | `rpc.arrowrpc.com` |
| 8453 | Base | `base.daybreak-rpc.network`, `rpc.swiftnodes.io/…?key=${SWIFTNODES_API_KEY}`, `api.blockvectra.com/v1/base_mainnet/public` | — |
| 42161 | Arbitrum One | `rpc.swiftnodes.io/…?key=${SWIFTNODES_API_KEY}`, `api.blockvectra.com/v1/arb_mainnet/public` | — |
| 43114 | Avalanche | `rpc.swiftnodes.io/…?key=${SWIFTNODES_API_KEY}` | — |
| 56 | BSC (not measured) | `rpc.backrunshield.com`, `rpc.swiftnodes.io/…?key=${SWIFTNODES_API_KEY}`, `api.blockvectra.com/v1/bsc_mainnet/public` | — |

None of these changes touches an endpoint that served logs in the measurement (`output/rpc_selection.json`). The
removed `rpc.arrowrpc.com` was not selected for Robinhood Chain. The `${…}` URLs are filtered out by the scanner. Without
`output/chainlist.json`, `select` fetches today's list and could try the new keyless endpoints as candidates. Fetching
the pinned version first (top of this file) makes `select` see the same candidates as the 13 October run.

Across the whole list, 50 entries were added, none removed and 53 changed between the two versions. Only the 27
entries above matter to the scanner.

## Why the file is not republished

The upstream list contains two RPC URLs with embedded basic-auth credentials (chainIds 8098 and 67390) and 13 ENS
registry addresses (`ens.registry` of 13 chains). Upstream publishes them, but this repository does not redistribute
them. None of them is used by the measurement. The ten-line table above, together with `output/rpc_selection.json`,
records every part of the list that the measurement relied on.
