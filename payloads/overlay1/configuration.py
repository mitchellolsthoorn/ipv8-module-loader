from ipv8.attestation.trustchain.settings import TrustChainSettings

tc_settings = TrustChainSettings()
tc_settings.crawler = True
tc_settings.max_db_blocks = 1000000000

extra_communities = None

config = {
    'overlays': [
        {
            'class': 'DiscoveryCommunity',
            'key': "my peer",
            'walkers': [
                {
                    'strategy': "RandomWalk",
                    'peers': -1,
                    'init': {
                        'timeout': 3.0
                    }
                },
                {
                    'strategy': "RandomChurn",
                    'peers': -1,
                    'init': {
                        'sample_size': 64,
                        'ping_interval': 1.0,
                        'inactive_time': 1.0,
                        'drop_time': 3.0
                    }
                }
            ],
            'initialize': {},
            'on_start': [
                ('resolve_dns_bootstrap_addresses', )
            ]
        }, {
            'class': 'TrustChainCommunity',
            'key': "my peer",
            'walkers': [
                {
                    'strategy': "RandomWalk",
                    'peers': -1,
                    'init': {
                        'timeout': 3.0
                    }
                },
            ],
            'initialize': {
                'settings': tc_settings
            },
            'on_start': [],
        },
    ]
}