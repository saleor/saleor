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
import StatusLabel from "../../../components/StatusLabel";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";
import { renderCollection } from "../../../misc";

interface PageListProps extends ListProps {
  pages?: Array<{
    id: string;
    title: string;
    slug: string;
    isVisible: boolean;
  }>;
}

const decorate = withStyles(theme => ({
  link: {
    color: theme.palette.secondary.main,
    cursor: "pointer" as "pointer",
    textDecoration: "none"
  },
  textRight: {
    textAlign: "right" as "right"
  }
}));

export const PageList = decorate<PageListProps>(
  ({
    classes,
    disabled,
    pageInfo,
    pages,
    onNextPage,
    onPreviousPage,
    onRowClick
  }) => (
    <Card>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>{i18n.t("Name", { context: "object" })}</TableCell>
            <TableCell>{i18n.t("Url", { context: "object" })}</TableCell>
            <TableCell>{i18n.t("Visibility", { context: "object" })}</TableCell>
          </TableRow>
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={3}
              hasNextPage={pageInfo && !disabled ? pageInfo.hasNextPage : false}
              hasPreviousPage={
                pageInfo && !disabled ? pageInfo.hasPreviousPage : false
              }
              onNextPage={onNextPage}
              onPreviousPage={onPreviousPage}
            />
          </TableRow>
        </TableFooter>
        <TableBody>
          {renderCollection(
            pages,
            page => (
              <TableRow key={page ? page.id : "skeleton"}>
                <TableCell
                  onClick={page && onRowClick(page.id)}
                  className={classes.link}
                >
                  {page ? page.title : <Skeleton />}
                </TableCell>
                <TableCell>{page ? `/${page.slug}` : <Skeleton />}</TableCell>
                <TableCell>
                  {page ? (
                    <StatusLabel
                      label={
                        page.isVisible
                          ? i18n.t("Published", { context: "object" })
                          : i18n.t("Not published", { context: "object" })
                      }
                      status={page.isVisible ? "success" : "error"}
                    />
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
              </TableRow>
            ),
            () => (
              <TableRow>
                <TableCell colSpan={3}>{i18n.t("No pages found")}</TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
PageList.displayName = "PageList";
export default PageList;
