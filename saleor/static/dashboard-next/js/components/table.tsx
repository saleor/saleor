import * as React from "react";
import MuiTable, {
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TablePagination,
  TableRow
} from "material-ui/Table";
import Typography from "material-ui/Typography";
import { withStyles } from "material-ui/styles";

interface TableProps {
  count: number;
  handleChangePage(
    event: React.MouseEvent<HTMLButtonElement> | null,
    page: number
  );
  handleRowClick(rowId: number);
  headers: Array<{
    label: string;
    name: string;
    wide?: boolean;
  }>;
  page: number;
  rowsPerPage: number;
  rowsPerPageOptions: Array<number>;
}

export const Table = props => {
  const {
    children,
    classes,
    count,
    handleChangePage,
    handleRowClick,
    headers,
    page,
    rowsPerPage,
    rowsPerPageOptions
  } = props;
  return (
    <MuiTable>
      <TableHead>
        <TableRow>
          {headers.map(header => (
            <TableCell key={header.name}>{header.label}</TableCell>
          ))}
        </TableRow>
      </TableHead>
      <TableBody>{children}</TableBody>
      <TableFooter>
        <TableRow>
          <TablePagination
            colSpan={5}
            count={count}
            onChangePage={handleChangePage}
            page={page}
            rowsPerPage={rowsPerPage}
            rowsPerPageOptions={rowsPerPageOptions}
          />
        </TableRow>
      </TableFooter>
    </MuiTable>
  );
};
