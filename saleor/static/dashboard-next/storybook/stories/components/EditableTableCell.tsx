import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import { storiesOf } from "@storybook/react";
import * as React from "react";

import EditableTableCell from "../../../components/EditableTableCell";
import Decorator from "../../Decorator";

storiesOf("Generics / EditableTableCell", module)
  .addDecorator(Decorator)
  .add("default", () => (
    <Table>
      <TableHead>
        <TableCell>Some header</TableCell>
        <TableCell>Some header</TableCell>
        <TableCell>Some header</TableCell>
      </TableHead>
      <TableBody>
        <TableRow>
          <TableCell>Some value</TableCell>
          <EditableTableCell
            value={"Some editable text"}
            onConfirm={() => undefined}
          />
          <TableCell>Some value</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  ));
