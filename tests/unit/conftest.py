import pathlib

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from buildingmotif import BuildingMOTIF, get_building_motif
from buildingmotif.database.tables import Base as BuildingMotif_tables_base
from buildingmotif.dataclasses.library import Library
from buildingmotif.dataclasses.template import Template


class MockBuildingMotif:
    """BuildingMOTIF for testing connections.

    Not a singletion, no connections classes, just the engine and connection. So
    we can pass this to the connections.
    """

    def __init__(self) -> None:
        """Class constructor."""
        self.engine = create_engine("sqlite://", echo=False)
        Session = sessionmaker(bind=self.engine, autoflush=True)
        self.session = Session()

        # add tables to db
        BuildingMotif_tables_base.metadata.create_all(self.engine)

    def close(self) -> None:
        """Close session and engine."""
        self.session.close()
        self.engine.dispose()


class MockLibrary(Library):
    """
    Mock library that always returns the requested template.
    """

    @classmethod
    def create(cls, name: str) -> "MockLibrary":
        bm = get_building_motif()
        db_library = bm.table_connection.create_db_library(name)
        return cls(_id=db_library.id, _name=db_library.name, _bm=bm)

    def get_template_by_name(self, name: str) -> Template:
        """
        Get the requested template by name or create it if it doesn't exist.
        TODO: do we need to mock the template to have arbitrary parameters?
        """
        try:
            return super().get_template_by_name(name)
        except Exception:
            return self.create_template(name)


@pytest.fixture
def bm():
    """
    BuildingMotif instance for tests involving dataclasses and API calls
    """
    bm = BuildingMOTIF("sqlite://")
    # add tables to db
    BuildingMotif_tables_base.metadata.create_all(bm.engine)

    yield bm
    bm.close()
    # clean up the singleton so that tables are re-created correctly later
    BuildingMOTIF.clean()


def pytest_generate_tests(metafunc):
    """
    Generates BuildingMOTIF tests for a variety of contexts
    """

    # validates that example files pass validation
    if "library" in metafunc.fixturenames:
        libdir = pathlib.Path("libraries")
        libraries_files = libdir.rglob("*.yml")
        libraries = {str(lib.parent) for lib in libraries_files}

        metafunc.parametrize("library", libraries)
