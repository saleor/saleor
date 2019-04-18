import Card from "@material-ui/core/Card";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import Typography from "@material-ui/core/Typography";
import * as classNames from "classnames";
import * as React from "react";

import Skeleton from "../../../components/Skeleton";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";
import { getUserName, maybe, renderCollection } from "../../../misc";
import { ListProps } from "../../../types";
import { StaffList_staffUsers_edges_node } from "../../types/StaffList";

const styles = (theme: Theme) =>
  createStyles({
    avatar: {
      alignItems: "center",
      borderRadius: "100%",
      display: "grid",
      float: "left",
      height: 47,
      justifyContent: "center",
      marginRight: theme.spacing.unit * 1 + "px",
      width: 37
    },
    avatarImage: {
      pointerEvents: "none",
      width: "100%"
    },
    statusText: {
      color: "#9E9D9D"
    },
    tableRow: {
      cursor: "pointer"
    },
    wideColumn: {
      width: "80%"
    }
  });

interface StaffListProps extends ListProps, WithStyles<typeof styles> {
  staffMembers: StaffList_staffUsers_edges_node[];
}

const StaffList = withStyles(styles, { name: "StaffList" })(
  ({
    classes,
    disabled,
    onNextPage,
    onPreviousPage,
    onRowClick,
    pageInfo,
    staffMembers
  }: StaffListProps) => (
    <Card>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell className={classes.wideColumn}>
              {i18n.t("Name", { context: "object" })}
            </TableCell>
            <TableCell>
              {i18n.t("Email Address", { context: "object" })}
            </TableCell>
          </TableRow>
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={3}
              hasNextPage={
                pageInfo && !disabled ? pageInfo.hasNextPage : undefined
              }
              onNextPage={onNextPage}
              hasPreviousPage={
                pageInfo && !disabled ? pageInfo.hasPreviousPage : undefined
              }
              onPreviousPage={onPreviousPage}
            />
          </TableRow>
        </TableFooter>
        <TableBody>
          {renderCollection(
            staffMembers,
            staffMember => (
              <TableRow
                className={classNames({
                  [classes.tableRow]: !!staffMember
                })}
                hover={!!staffMember}
                onClick={!!staffMember ? onRowClick(staffMember.id) : undefined}
                key={staffMember ? staffMember.id : "skeleton"}
              >
                <TableCell>
                  <div className={classes.avatar}>
                    <img
                      className={classes.avatarImage}
                      src={maybe(() => staffMember.avatar.url)}
                    />
                  </div>
                  <Typography>
                    {getUserName(staffMember) || <Skeleton />}
                  </Typography>
                  <Typography
                    variant={"caption"}
                    className={classes.statusText}
                  >
                    {maybe<React.ReactNode>(
                      () =>
                        staffMember.isActive
                          ? i18n.t("Active", { context: "status" })
                          : i18n.t("Inactive", { context: "status" }),
                      <Skeleton />
                    )}
                  </Typography>
                </TableCell>
                <TableCell>
                  {maybe<React.ReactNode>(
                    () => staffMember.email,
                    <Skeleton />
                  )}
                </TableCell>
              </TableRow>
            ),
            () => (
              <TableRow>
                <TableCell colSpan={3}>
                  {i18n.t("No staff members found")}
                </TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
StaffList.displayName = "StaffList";
export default StaffList;
