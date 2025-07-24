[Eth]
NetworkId = %{ if network == "mainnet" }1%{ else if network == "goerli" }5%{ else if network == "sepolia" }11155111%{ else if network == "holesky" }17000%{ endif }
SyncMode = "light"

[Node]
HTTPHost = "0.0.0.0"
HTTPPort = ${rpc_port}
HTTPModules = ["eth", "net", "web3", "debug"]
HTTPCors = ["*"]
HTTPVirtualHosts = ["*"]

WSHost = "0.0.0.0"
WSPort = ${ws_port}
WSModules = ["eth", "net", "web3"]
WSOrigins = ["*"]

[Node.P2P]
MaxPeers = 50
MaxPendingPeers = 0

[Node.HTTPTimeouts]
ReadTimeout = 30s
WriteTimeout = 30s
IdleTimeout = 120s

[Metrics]
Enabled = true
HTTP = "0.0.0.0:6060"

[Database]
Cache = 512
Handles = 512

[Eth.Miner]
GasPrice = 1000000000

# Limit blocks for testing
[Eth.TxPool]
AccountSlots = 16
GlobalSlots = 4096
AccountQueue = 64
GlobalQueue = 1024
Lifetime = 3h

# Custom block limit for testing
[Eth.BlockChain]
MaxBlocks = ${max_blocks} 