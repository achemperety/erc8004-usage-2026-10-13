# Addendum C, 11 November 2026: owner of the agent at the block of each validation request

This addendum changes no result of the 13 October 2026 measurement. The original owner check stays as it was:
`output/self_validation_check.json`, read at block tag `latest` at about 13:57 UTC on 13 October 2026. This addendum reads
the owner again **at the block of each request** and reports both side by side.

## Scope and method

- **Requests:** every `ValidationRequest` recorded on Base (15), Mantle (10), 0G (14),
  Monad (5) and Celo (21, a lower bound): 65 in all, which is every validation request the
  13 October scan found. They are taken from `output/counts/<chainId>_validation_ValidationRequest.json`. `validator`
  is topic1 and `agentId` is topic2 of each log.
- **Read:** `eth_call` of `ownerOf(agentId)` (selector `0x6352211e`) on the Identity registry
  `0x8004A169FB4a3325136EB29fA0ceB6D2e539a432`, with the request's block number as the block parameter. This gives the
  state **after all transactions of that block**. In the same call round, `eth_getCode` of the registry at that block
  checks that the endpoint really has state there. A pruned node that answers with empty state is not counted as an
  answer.
- **Endpoints:** every public, keyless endpoint listed in the script was asked about every request. An endpoint that gave
  no usable answer for three requests in a row on a chain was skipped for the rest of that chain, and this is recorded.
  A request that was still undetermined after the first pass was retried once on every endpoint that had failed with a
  transport or HTTP error. Both attempts are kept in the JSON (0 retries in this run).
- **Rule:** a request counts as **determined** only if **at least two endpoints** returned an owner and all endpoints
  that answered agree. Otherwise it is "not determined", and the reason is recorded.
- **Run:** 2026-11-11, 2026-11-11T11:22:52Z to 2026-11-11T11:24:23Z. Read-only calls only (`eth_chainId`,
  `eth_getCode`, `eth_call`).
- **Code and raw output:** `addenda/2026-11-11_owner_at_request_block.py` and
  `addenda/2026-11-11_owner_at_request_block.json`, with each endpoint's raw response per request.

## Result per chain

| chain | requests | determined | not determined | validator == owner at request block | validator == owner at latest read (13 Oct, ~13:57 UTC) | owner changed between request block and latest read |
|---|---:|---:|---:|---:|---:|---:|
| Base | 15 | 15 | 0 | 14 of 15 | 14 of 15 | 0 |
| Mantle | 10 | 10 | 0 | 10 of 10 | 10 of 10 | 0 |
| 0G | 14 | 14 | 0 | 14 of 14 | 10 of 14 | 4 |
| Monad | 5 | 5 | 0 | 2 of 5 | 2 of 5 | 0 |
| Celo | 21 | 21 | 0 | 0 of 21 | 0 of 21 | 0 |

**All 65 requests were determined**, each by at least 2 endpoints that agreed.

- **Base, Mantle, Monad, Celo:** wherever a request was determined, the owner at the request block is the same address as at the
  13 October latest read.
- **0G differs.** At the block of each request, the validator was the agent's owner for every determined 0G request.
  The 13 October `latest` read had shown 10 of 14, because these agents changed owner afterwards:

| chain | block | agentId | validator | owner at request block | owner at latest read, 13 Oct |
|---|---:|---:|---|---|---|
| 0G | 38894992 | 2179684 | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | `0x9a4d42e1ad15688ecb6f7fe0f1a4930cb11aec2f` |
| 0G | 38895332 | 2179636 | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | `0x6b51256e2a8e746d771763b4c274f17aa65f4922` |
| 0G | 38895365 | 2179652 | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | `0x5563196240bfb38c0c320b146293cb8fd24d5148` |
| 0G | 38895397 | 2179655 | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | `0xb92f4d4219de3c969498c9dec7563bc77be102ba` |

Each of these transfers happened after the request's block and before about 13:57 UTC on 13 October 2026. This
addendum does not identify the transactions.

## Endpoint behaviour

| chain | endpoint | owner | reverted | no_state | empty | error | skipped |
|---|---|---:|---:|---:|---:|---:|---:|
| Base | `1rpc.io/base` | 0 | 0 | 3 | 0 | 0 | 12 |
| Base | `base-rpc.publicnode.com` | 0 | 0 | 0 | 0 | 3 | 12 |
| Base | `base.drpc.org` | 13 | 0 | 0 | 0 | 2 | 0 |
| Base | `base.gateway.tenderly.co` | 15 | 0 | 0 | 0 | 0 | 0 |
| Base | `mainnet.base.org` | 15 | 0 | 0 | 0 | 0 | 0 |
| Mantle | `1rpc.io/mantle` | 0 | 0 | 0 | 0 | 3 | 7 |
| Mantle | `mantle-rpc.publicnode.com` | 0 | 0 | 3 | 0 | 0 | 7 |
| Mantle | `mantle.drpc.org` | 10 | 0 | 0 | 0 | 0 | 0 |
| Mantle | `rpc.mantle.xyz` | 10 | 0 | 0 | 0 | 0 | 0 |
| 0G | `0g.drpc.org` | 14 | 0 | 0 | 0 | 0 | 0 |
| 0G | `evmrpc.0g.ai` | 14 | 0 | 0 | 0 | 0 | 0 |
| Monad | `monad-mainnet.drpc.org` | 0 | 0 | 0 | 0 | 3 | 2 |
| Monad | `rpc.monad.xyz` | 5 | 0 | 0 | 0 | 0 | 0 |
| Monad | `rpc1.monad.xyz` | 5 | 0 | 0 | 0 | 0 | 0 |
| Monad | `rpc2.monad.xyz` | 5 | 0 | 0 | 0 | 0 | 0 |
| Monad | `rpc3.monad.xyz` | 0 | 0 | 3 | 0 | 0 | 2 |
| Celo | `1rpc.io/celo` | 1 | 0 | 2 | 1 | 0 | 17 |
| Celo | `celo-rpc.publicnode.com` | 0 | 0 | 0 | 0 | 3 | 18 |
| Celo | `celo.drpc.org` | 21 | 0 | 0 | 0 | 0 | 0 |
| Celo | `forno.celo.org` | 21 | 0 | 0 | 0 | 0 | 0 |

- `no_state` means the endpoint reported pruned or unavailable historical state.
- `empty` means it returned `0x`, or the registry had no code at that block on that endpoint.
- `error` means a transport or HTTP error, such as 403 or a TLS timeout, on either call.
- `skipped` means the endpoint was skipped after three non-answers in a row. For a retried endpoint, the table counts the
  final attempt.

## Every request

| chain | block | agentId | validator | owner at request block | validator = owner (request block) | owner at latest read | validator = owner (latest) | endpoints that answered |
|---|---:|---:|---|---|---|---|---|---|
| Base | 43134133 | 25331 | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | yes | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | yes | base.drpc.org, base.gateway.tenderly.co, mainnet.base.org |
| Base | 43134146 | 25331 | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | yes | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | yes | base.drpc.org, base.gateway.tenderly.co, mainnet.base.org |
| Base | 43134682 | 25331 | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | yes | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | yes | base.drpc.org, base.gateway.tenderly.co, mainnet.base.org |
| Base | 43134858 | 25331 | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | yes | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | yes | base.drpc.org, base.gateway.tenderly.co, mainnet.base.org |
| Base | 43134870 | 25331 | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | yes | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | yes | base.drpc.org, base.gateway.tenderly.co, mainnet.base.org |
| Base | 43135041 | 25331 | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | yes | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | yes | base.drpc.org, base.gateway.tenderly.co, mainnet.base.org |
| Base | 43138402 | 25331 | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | yes | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | yes | base.gateway.tenderly.co, mainnet.base.org |
| Base | 43138830 | 25331 | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | yes | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | yes | base.gateway.tenderly.co, mainnet.base.org |
| Base | 43140910 | 25331 | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | yes | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | yes | base.drpc.org, base.gateway.tenderly.co, mainnet.base.org |
| Base | 43177272 | 25331 | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | yes | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | yes | base.drpc.org, base.gateway.tenderly.co, mainnet.base.org |
| Base | 43181588 | 25331 | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | yes | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | yes | base.drpc.org, base.gateway.tenderly.co, mainnet.base.org |
| Base | 43183045 | 25331 | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | yes | `0xc5b29033e63a986b601fe430806a2c9735f2ea97` | yes | base.drpc.org, base.gateway.tenderly.co, mainnet.base.org |
| Base | 50073293 | 60102 | `0x3a77efd0f47907a32ee9f5c90d9ec91ba7fca4c3` | `0xb82a61b2871b221a4a261180dbec042395a60dfb` | no | `0xb82a61b2871b221a4a261180dbec042395a60dfb` | no | base.drpc.org, base.gateway.tenderly.co, mainnet.base.org |
| Base | 51606429 | 95265 | `0x0c3a19bea92480a978f2a358e8e1e87b9dad14b5` | `0x0c3a19bea92480a978f2a358e8e1e87b9dad14b5` | yes | `0x0c3a19bea92480a978f2a358e8e1e87b9dad14b5` | yes | base.drpc.org, base.gateway.tenderly.co, mainnet.base.org |
| Base | 51702363 | 95374 | `0x6328f2fe483922721d94b33ee99e9938da3b7911` | `0x6328f2fe483922721d94b33ee99e9938da3b7911` | yes | `0x6328f2fe483922721d94b33ee99e9938da3b7911` | yes | base.drpc.org, base.gateway.tenderly.co, mainnet.base.org |
| Mantle | 96827854 | 134 | `0x36599b0286d3c32f934bc8877eea839d88f3affc` | `0x36599b0286d3c32f934bc8877eea839d88f3affc` | yes | `0x36599b0286d3c32f934bc8877eea839d88f3affc` | yes | mantle.drpc.org, rpc.mantle.xyz |
| Mantle | 96916516 | 134 | `0x36599b0286d3c32f934bc8877eea839d88f3affc` | `0x36599b0286d3c32f934bc8877eea839d88f3affc` | yes | `0x36599b0286d3c32f934bc8877eea839d88f3affc` | yes | mantle.drpc.org, rpc.mantle.xyz |
| Mantle | 96918956 | 136 | `0x9c0bd9b60ea840347b2731aa630d387bbd56e075` | `0x9c0bd9b60ea840347b2731aa630d387bbd56e075` | yes | `0x9c0bd9b60ea840347b2731aa630d387bbd56e075` | yes | mantle.drpc.org, rpc.mantle.xyz |
| Mantle | 96919121 | 136 | `0x9c0bd9b60ea840347b2731aa630d387bbd56e075` | `0x9c0bd9b60ea840347b2731aa630d387bbd56e075` | yes | `0x9c0bd9b60ea840347b2731aa630d387bbd56e075` | yes | mantle.drpc.org, rpc.mantle.xyz |
| Mantle | 96919133 | 136 | `0x9c0bd9b60ea840347b2731aa630d387bbd56e075` | `0x9c0bd9b60ea840347b2731aa630d387bbd56e075` | yes | `0x9c0bd9b60ea840347b2731aa630d387bbd56e075` | yes | mantle.drpc.org, rpc.mantle.xyz |
| Mantle | 96919161 | 136 | `0x9c0bd9b60ea840347b2731aa630d387bbd56e075` | `0x9c0bd9b60ea840347b2731aa630d387bbd56e075` | yes | `0x9c0bd9b60ea840347b2731aa630d387bbd56e075` | yes | mantle.drpc.org, rpc.mantle.xyz |
| Mantle | 96919173 | 136 | `0x9c0bd9b60ea840347b2731aa630d387bbd56e075` | `0x9c0bd9b60ea840347b2731aa630d387bbd56e075` | yes | `0x9c0bd9b60ea840347b2731aa630d387bbd56e075` | yes | mantle.drpc.org, rpc.mantle.xyz |
| Mantle | 96919183 | 136 | `0x9c0bd9b60ea840347b2731aa630d387bbd56e075` | `0x9c0bd9b60ea840347b2731aa630d387bbd56e075` | yes | `0x9c0bd9b60ea840347b2731aa630d387bbd56e075` | yes | mantle.drpc.org, rpc.mantle.xyz |
| Mantle | 96919195 | 136 | `0x9c0bd9b60ea840347b2731aa630d387bbd56e075` | `0x9c0bd9b60ea840347b2731aa630d387bbd56e075` | yes | `0x9c0bd9b60ea840347b2731aa630d387bbd56e075` | yes | mantle.drpc.org, rpc.mantle.xyz |
| Mantle | 97174516 | 134 | `0x36599b0286d3c32f934bc8877eea839d88f3affc` | `0x36599b0286d3c32f934bc8877eea839d88f3affc` | yes | `0x36599b0286d3c32f934bc8877eea839d88f3affc` | yes | mantle.drpc.org, rpc.mantle.xyz |
| 0G | 38894992 | 2179684 | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | yes | `0x9a4d42e1ad15688ecb6f7fe0f1a4930cb11aec2f` | no | 0g.drpc.org, evmrpc.0g.ai |
| 0G | 38895037 | 2179710 | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | yes | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | yes | 0g.drpc.org, evmrpc.0g.ai |
| 0G | 38895069 | 2179717 | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | yes | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | yes | 0g.drpc.org, evmrpc.0g.ai |
| 0G | 38895102 | 2179735 | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | yes | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | yes | 0g.drpc.org, evmrpc.0g.ai |
| 0G | 38895134 | 2179766 | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | yes | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | yes | 0g.drpc.org, evmrpc.0g.ai |
| 0G | 38895166 | 2179768 | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | yes | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | yes | 0g.drpc.org, evmrpc.0g.ai |
| 0G | 38895197 | 2179854 | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | yes | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | yes | 0g.drpc.org, evmrpc.0g.ai |
| 0G | 38895235 | 2179858 | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | yes | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | yes | 0g.drpc.org, evmrpc.0g.ai |
| 0G | 38895269 | 2179861 | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | yes | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | yes | 0g.drpc.org, evmrpc.0g.ai |
| 0G | 38895300 | 2179869 | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | yes | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | yes | 0g.drpc.org, evmrpc.0g.ai |
| 0G | 38895332 | 2179636 | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | yes | `0x6b51256e2a8e746d771763b4c274f17aa65f4922` | no | 0g.drpc.org, evmrpc.0g.ai |
| 0G | 38895365 | 2179652 | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | yes | `0x5563196240bfb38c0c320b146293cb8fd24d5148` | no | 0g.drpc.org, evmrpc.0g.ai |
| 0G | 38895397 | 2179655 | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | yes | `0xb92f4d4219de3c969498c9dec7563bc77be102ba` | no | 0g.drpc.org, evmrpc.0g.ai |
| 0G | 38895428 | 2179661 | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | yes | `0x929d7e2448a60b1eb70766bb35a620504f9bc972` | yes | 0g.drpc.org, evmrpc.0g.ai |
| Monad | 106470714 | 10252 | `0xdb6c6340342e71a63cd11ebac2185204b7777777` | `0xdb6c6340342e71a63cd11ebac2185204b7777777` | yes | `0xdb6c6340342e71a63cd11ebac2185204b7777777` | yes | rpc.monad.xyz, rpc1.monad.xyz, rpc2.monad.xyz |
| Monad | 110872153 | 10280 | `0x77a55a4980769f543ea5bb799f4f49a8c1cd0d85` | `0x4f3f999b60750cef97d7d56c75f30f050a583d53` | no | `0x4f3f999b60750cef97d7d56c75f30f050a583d53` | no | rpc.monad.xyz, rpc1.monad.xyz, rpc2.monad.xyz |
| Monad | 111383397 | 10315 | `0x77a55a4980769f543ea5bb799f4f49a8c1cd0d85` | `0xb925d44d52815d19c2f91c30f6abd3b4d0546d4e` | no | `0xb925d44d52815d19c2f91c30f6abd3b4d0546d4e` | no | rpc.monad.xyz, rpc1.monad.xyz, rpc2.monad.xyz |
| Monad | 111384578 | 10315 | `0x77a55a4980769f543ea5bb799f4f49a8c1cd0d85` | `0xb925d44d52815d19c2f91c30f6abd3b4d0546d4e` | no | `0xb925d44d52815d19c2f91c30f6abd3b4d0546d4e` | no | rpc.monad.xyz, rpc1.monad.xyz, rpc2.monad.xyz |
| Monad | 112814384 | 10386 | `0x9f0af03c5695b72903c03852f7dd4fe5a0d49fc9` | `0x9f0af03c5695b72903c03852f7dd4fe5a0d49fc9` | yes | `0x9f0af03c5695b72903c03852f7dd4fe5a0d49fc9` | yes | rpc.monad.xyz, rpc1.monad.xyz, rpc2.monad.xyz |
| Celo | 62018062 | 1870 | `0xeed513498cf755bafa9fd13c36b178d70f27ab71` | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | 1rpc.io, celo.drpc.org, forno.celo.org |
| Celo | 62018107 | 1870 | `0xa20a6d4e84d3ac4581166f819867c8c83a606282` | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | celo.drpc.org, forno.celo.org |
| Celo | 62018152 | 1870 | `0x43b8ab8d79d1b1c448df34d503719280f1d08779` | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | celo.drpc.org, forno.celo.org |
| Celo | 62018215 | 1870 | `0x7b1b2573787a3d9465fd13b6f4466e711a016b50` | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | celo.drpc.org, forno.celo.org |
| Celo | 62018311 | 1870 | `0xb9116f95c9495ae03887d5a47f675478e3c9ba49` | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | celo.drpc.org, forno.celo.org |
| Celo | 62018359 | 1870 | `0x09a00d2f4cac819ab9515d9798f1f7c20c068f0d` | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | celo.drpc.org, forno.celo.org |
| Celo | 62018407 | 1870 | `0xe165595dbdb02c41bf137e42877198567361a55e` | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | celo.drpc.org, forno.celo.org |
| Celo | 62018454 | 1870 | `0xf44e9e527d58f8a3c3aff0eb1eb70feeb41b938a` | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | celo.drpc.org, forno.celo.org |
| Celo | 62018501 | 1870 | `0xc72bebf9c42d527256c1e48cd1ed9d743487fb01` | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | celo.drpc.org, forno.celo.org |
| Celo | 62018557 | 1870 | `0x2d1b460334dc42cf74acb76093e7c2a912877325` | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | celo.drpc.org, forno.celo.org |
| Celo | 62018605 | 1870 | `0xdbfd92488e74d2da1ba73bf07935e3e455f970ee` | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | celo.drpc.org, forno.celo.org |
| Celo | 62018651 | 1870 | `0x075199c4a9dbd6f4688d07524499845181bee10e` | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | celo.drpc.org, forno.celo.org |
| Celo | 62055167 | 1870 | `0x5c1a4df7f122312904d4d353e8666154afe17742` | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | celo.drpc.org, forno.celo.org |
| Celo | 62055335 | 1870 | `0x4a9053d29d5a2a8bb9c62154eb3eedde909a4be8` | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | celo.drpc.org, forno.celo.org |
| Celo | 62055384 | 1870 | `0x3fa1ef1f10c0b8c2a2020643b5ffc2bc6e85ed57` | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | celo.drpc.org, forno.celo.org |
| Celo | 62055430 | 1870 | `0xbacf92c3d7a37d70321b28901e73e554beff0bd3` | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | celo.drpc.org, forno.celo.org |
| Celo | 62055474 | 1870 | `0xa852af9312f480e8fb5aa50b44fa8ddd7f149d3e` | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | celo.drpc.org, forno.celo.org |
| Celo | 62055526 | 1870 | `0x71471766891fbf6778c3a988b6bb18c19ac726e3` | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | celo.drpc.org, forno.celo.org |
| Celo | 62055577 | 1870 | `0x0c22301c76fdd2d7a81027e6a972b4a0afc5c32e` | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | celo.drpc.org, forno.celo.org |
| Celo | 62055627 | 1870 | `0x29d6b77e6def78b4262f4ba2bb1399b0528fdeb4` | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | celo.drpc.org, forno.celo.org |
| Celo | 62055678 | 1870 | `0x32f558f889cb3e5cd229010e9e5028b9dc296023` | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | `0x558e7bfaf2cf1a494f44e50d92431afc060c9d12` | no | celo.drpc.org, forno.celo.org |

## What this establishes, and what it does not

- **Establishes:** for each determined request, which address held the agent token in the state right after the
  request's block, and whether that address was the validator named in the request.
- **Does not establish** that owner and validator are the same person or organisation, or that different addresses are
  independent. One operator can control several addresses.
- **Does not establish** the quality or content of any response, or anything about requests that the 13 October scan did
  not see. Celo remains a lower bound.
- **Same-block transfers:** the state read is after the request's block. If the token were transferred later in the same
  block, after the request transaction, the owner reported here would differ from the owner at the moment of the
  request. Block-level reads cannot rule this out.
