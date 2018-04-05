import Table from "material-ui/Table";
import * as React from "react";
import * as renderer from "react-test-renderer";

import TablePagination from "./TablePagination";

describe("<TablePagination />", () => {
  it("renders when no previous / next page are available", () => {
    const component = renderer.create(
      <Table>
        <TablePagination
          colSpan={1}
          hasNextPage={false}
          hasPreviousPage={false}
          onPreviousPage={jest.fn()}
          onNextPage={jest.fn()}
        />
      </Table>
    );
    expect(component).toMatchSnapshot();
  });
  it("renders when previous page is available", () => {
    const component = renderer.create(
      <Table>
        <TablePagination
          colSpan={1}
          hasNextPage={false}
          hasPreviousPage={true}
          onPreviousPage={jest.fn()}
          onNextPage={jest.fn()}
        />
      </Table>
    );
    expect(component).toMatchSnapshot();
  });
  it("renders when next page is available", () => {
    const component = renderer.create(
      <Table>
        <TablePagination
          colSpan={1}
          hasNextPage={true}
          hasPreviousPage={false}
          onPreviousPage={jest.fn()}
          onNextPage={jest.fn()}
        />
      </Table>
    );
    expect(component).toMatchSnapshot();
  });
  it("renders when previous and next pages are available", () => {
    const component = renderer.create(
      <Table>
        <TablePagination
          colSpan={1}
          hasNextPage={true}
          hasPreviousPage={true}
          onPreviousPage={jest.fn()}
          onNextPage={jest.fn()}
        />
      </Table>
    );
    expect(component).toMatchSnapshot();
  });
});
