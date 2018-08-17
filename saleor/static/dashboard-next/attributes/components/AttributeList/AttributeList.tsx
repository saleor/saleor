import Card from "@material-ui/core/Card";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import { ListProps } from "../../..";
import Skeleton from "../../../components/Skeleton";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";
import { renderCollection } from "../../../misc";

interface AttributeListProps extends ListProps {
  attributes?: Array<{
    id: string;
    name: string;
    values: Array<{
      id: string;
      sortOrder: number;
      name: string;
    }>;
  }>;
}

const decorate = withStyles(theme => ({
  link: {
    color: theme.palette.secondary.main,
    cursor: "pointer"
  }
}));
const AttributeList = decorate<AttributeListProps>(
  ({
    attributes,
    classes,
    disabled,
    pageInfo,
    onNextPage,
    onPreviousPage,
    onRowClick
  }) => (
    <Card>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>{i18n.t("Name", { context: "object" })}</TableCell>
            <TableCell>{i18n.t("Values", { context: "object" })}</TableCell>
          </TableRow>
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={2}
              hasNextPage={pageInfo && !disabled ? pageInfo.hasNextPage : false}
              onNextPage={onNextPage}
              hasPreviousPage={
                pageInfo && !disabled ? pageInfo.hasPreviousPage : false
              }
              onPreviousPage={onPreviousPage}
            />
          </TableRow>
        </TableFooter>
        <TableBody>
          {renderCollection(
            attributes,
            attribute => (
              <TableRow key={attribute ? attribute.id : "skeleton"}>
                <TableCell>
                  {attribute ? (
                    <span
                      onClick={onRowClick(attribute.id)}
                      className={classes.link}
                    >
                      {attribute.name}
                    </span>
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
                <TableCell>
                  {attribute && attribute.values ? (
                    attribute.values
                      .sort(
                        (a, b) =>
                          a.sortOrder > b.sortOrder
                            ? 1
                            : a.sortOrder < b.sortOrder
                              ? -1
                              : 0
                      )
                      .map(v => v.name)
                      .join(", ")
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
              </TableRow>
            ),
            () => (
              <TableRow>
                <TableCell colSpan={2}>
                  {i18n.t("No attributes found")}
                </TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
AttributeList.displayName = "AttributeList";
export default AttributeList;
