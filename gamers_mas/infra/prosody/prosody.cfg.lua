daemonize = false
pidfile = "/tmp/prosody.pid"

admins = { }

modules_enabled = {
    "roster";
    "saslauth";
    "tls";
}

authentication = "internal_hashed"
allow_registration = false

c2s_require_encryption = false
s2s_require_encryption = false

VirtualHost(os.getenv("XMPP_DOMAIN") or "localhost")
