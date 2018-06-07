import Card from "@material-ui/core/Card";
import blue from "@material-ui/core/colors/blue";
import IconButton from "@material-ui/core/IconButton";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import VisibilityIcon from "@material-ui/icons/Visibility";
import * as React from "react";

import Skeleton from "../../../components/Skeleton";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";

interface PageListComponentProps {
  pages?: Array<{
    id: string;
    title: string;
    slug: string;
    isVisible: boolean;
  }>;
  pageInfo?: {
    hasNextPage: boolean;
    hasPreviousPage: boolean;
  };
  onEditClick(id: string);
  onNextPage();
  onPreviousPage();
  onShowPageClick(slug: string);
}

const decorate = withStyles({
  link: {
    color: blue[500],
    cursor: "pointer",
    textDecoration: "none"
  },
  textRight: {
    textAlign: "right"
  }
});

export const PageListComponent = decorate<PageListComponentProps>(
  ({
    classes,
    onEditClick,
    onNextPage,
    onPreviousPage,
    onShowPageClick,
    pageInfo,
    pages
  }) => (
    <Card>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>{i18n.t("Name", { context: "object" })}</TableCell>
            <TableCell>{i18n.t("Url", { context: "object" })}</TableCell>
            <TableCell>{i18n.t("Visibility", { context: "object" })}</TableCell>
            <TableCell className={classes.textRight}>
              {i18n.t("Actions", { context: "object" })}
            </TableCell>
          </TableRow>
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={4}
              hasNextPage={pageInfo ? pageInfo.hasNextPage : false}
              hasPreviousPage={pageInfo ? pageInfo.hasPreviousPage : false}
              onNextPage={onNextPage}
              onPreviousPage={onPreviousPage}
            />
          </TableRow>
        </TableFooter>
        <TableBody>
          {pages === undefined || pages === null ? (
            <TableRow>
              <TableCell>
                <Skeleton />
              </TableCell>
              <TableCell>
                <Skeleton />
              </TableCell>
              <TableCell>
                <Skeleton />
              </TableCell>
              <TableCell className={classes.textRight}>
                <IconButton disabled>
                  <VisibilityIcon />
                </IconButton>
              </TableCell>
            </TableRow>
          ) : pages.length > 0 ? (
            pages.map(page => (
              <TableRow key={page.id}>
                <TableCell
                  onClick={onEditClick(page.id)}
                  className={classes.link}
                >
                  {page.title}
                </TableCell>
                <TableCell>{`/${page.slug}`}</TableCell>
                <TableCell>
                  {page.isVisible
                    ? i18n.t("Published", { context: "object" })
                    : i18n.t("Not published", { context: "object" })}
                </TableCell>
                <TableCell className={classes.textRight}>
                  <IconButton onClick={onShowPageClick(page.slug)}>
                    <VisibilityIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={4}>{i18n.t("No pages found")}</TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </Card>
  )
);

export default PageListComponent;
