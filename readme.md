# Homes - Server hosted at HOME
## Overview
*Homes* is a python implementation of [NAT traversal](https://en.wikipedia.org/wiki/NAT_traversal) technique, which provides public access to your domestic hosts behind NAT if you own a public server. The diagram indicates how it works.

```
Local <--[TCP]--> Client <--[Websocket]--> Server <--[TCP]--> User
(NAT)              (NAT)                 (Internet)        (Internet)
```

`Client` connects to `Server` actively and establishes a long Websocket connection. When `User` visits `Server`, `Client` acts as a proxy to visit `Local` and forwards data flow through `Server` between `Local` and `User`.

Secure connection over TLS between `Client` and `Server` is also  supported.

To protect privacy, only a hash of `User`'s socket address `(ip, port)` is shared between `Server` and `Client`, to differentiate multiple connections. Therefore, `User`'s real address is secret to `Local`. 

To use *Homes*, you need a server with a public IP. Then
+ Install and start *Homes* on your public server.
+ Install and start *Homes* on your local machine.
+ Start your local application.
+ Visit your local application through your public server.