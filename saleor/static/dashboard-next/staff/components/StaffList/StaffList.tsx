import Card from "@material-ui/core/Card";
import { withStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import Skeleton from "../../../components/Skeleton";
import StatusLabel from "../../../components/StatusLabel";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";

interface StaffListPageProps {
  staff?: Array<{
    id: string;
    email?: string;
    groups?: {
      totalCount: number;
    };
    isActive?: boolean;
  }>;
  pageInfo?: {
    hasNextPage: boolean;
    hasPreviousPage: boolean;
  };
  onNextPage?: () => void;
  onPreviousPage?: () => void;
  onRowClick?: (id: string) => () => void;
}

const decorate = withStyles(theme => ({
  link: {
    color: theme.palette.secondary.main,
    cursor: "pointer" as "pointer"
  },
  textRight: {
    textAlign: "right" as "right"
  }
}));
const StaffListPage = decorate<StaffListPageProps>(
  ({ classes, staff, pageInfo, onNextPage, onPreviousPage, onRowClick }) => (
    <Card>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>{i18n.t("E-mail")}</TableCell>
            <TableCell>{i18n.t("Status")}</TableCell>
            <TableCell className={classes.textRight}>
              {i18n.t("Groups")}
            </TableCell>
          </TableRow>
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={3}
              hasNextPage={pageInfo ? pageInfo.hasNextPage : false}
              hasPreviousPage={pageInfo ? pageInfo.hasPreviousPage : false}
              onNextPage={onNextPage}
              onPreviousPage={onPreviousPage}
            />
          </TableRow>
        </TableFooter>
        <TableBody>
          {staff === undefined || staff === null ? (
            <TableRow>
              <TableCell>
                <Skeleton />
              </TableCell>
              <TableCell>
                <Skeleton />
              </TableCell>
              <TableCell className={classes.textRight}>
                <Skeleton />
              </TableCell>
            </TableRow>
          ) : staff.length > 0 ? (
            staff.map(member => (
              <TableRow key={member.id}>
                <TableCell
                  onClick={
                    member.email && !!onRowClick
                      ? onRowClick(member.id)
                      : undefined
                  }
                  className={!!onRowClick && member.email ? classes.link : ""}
                >
                  {member.email === undefined ? <Skeleton /> : member.email}
                </TableCell>
                <TableCell>
                  {member.isActive === undefined ? (
                    <Skeleton />
                  ) : (
                    <StatusLabel
                      status={member.isActive ? "success" : "neutral"}
                      label={
                        member.isActive ? i18n.t("Active") : i18n.t("Inactive")
                      }
                    />
                  )}
                </TableCell>
                <TableCell className={classes.textRight}>
                  {member.groups && member.groups.totalCount === undefined ? (
                    <Skeleton />
                  ) : (
                    member.groups.totalCount
                  )}
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={3}>
                {i18n.t("No staff members found")}
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
StaffListPage.displayName = "StaffListPage";
export default StaffListPage;
