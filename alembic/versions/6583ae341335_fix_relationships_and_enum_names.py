"""Fix relationships and ENUM names

Revision ID: 6583ae341335
Revises: ac8dc96facfd
Create Date: 2024-09-14 17:09:44.689368

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6583ae341335"
down_revision: Union[str, None] = "ac8dc96facfd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
