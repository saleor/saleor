import { storiesOf } from "@storybook/react";
import Card from "material-ui/Card";
import Table, {
  TableBody,
  TableCell,
  TableHead,
  TableRow
} from "material-ui/Table";
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
            onConfirm={() => () => {}}
          />
          <TableCell>Some value</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  ));
