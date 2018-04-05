import { storiesOf } from "@storybook/react";
import Table from "material-ui/Table";
import * as React from "react";

import TablePagination from "../../../components/TablePagination";

storiesOf("Generics / TablePagination", module)
  .add("no previous / next page", () => (
    <Table>
      <TablePagination
        colSpan={1}
        hasNextPage={false}
        hasPreviousPage={false}
        onPreviousPage={() => {}}
        onNextPage={() => {}}
      />
    </Table>
  ))
  .add("previous page available", () => (
    <Table>
      <TablePagination
        colSpan={1}
        hasNextPage={false}
        hasPreviousPage={true}
        onPreviousPage={() => {}}
        onNextPage={() => {}}
      />
    </Table>
  ))
  .add("next page available", () => (
    <Table>
      <TablePagination
        colSpan={1}
        hasNextPage={true}
        hasPreviousPage={false}
        onPreviousPage={() => {}}
        onNextPage={() => {}}
      />
    </Table>
  ))
  .add("both previous and next pages are available", () => (
    <Table>
      <TablePagination
        colSpan={1}
        hasNextPage={true}
        hasPreviousPage={true}
        onPreviousPage={() => {}}
        onNextPage={() => {}}
      />
    </Table>
  ));
