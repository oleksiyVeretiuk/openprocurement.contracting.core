PARTIAL_MOCK_CONFIG = {
    "api": {
      "plugins": {
        "contracting.core": {
            "migration": False,
            "aliases": []
        },
        "transferring": {
            "plugins": {
                "contracting.transferring": None
            }
        }
      }
    }
}
