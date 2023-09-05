import os

if not os.path.exists(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "test_data"
    )
):
    os.mkdir(
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "test_data"
        )
    )
