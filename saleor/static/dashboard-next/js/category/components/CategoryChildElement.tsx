import * as React from "react";
import Grid from "material-ui/Grid";
import Card, { CardContent } from "material-ui/Card";
import Typography from "material-ui/Typography";
import { Link } from "react-router-dom";
import { Skeleton } from "../../components/Skeleton";
import { withStyles } from "material-ui/styles";

interface CategoryChildElementProps {
  label: string;
  url: string;
  loading?: boolean;
}

const decorate = withStyles(theme => ({
  link: {
    textDecoration: "none",
    color: theme.typography.body1.color
  }
}));
export const CategoryChildElement = decorate<CategoryChildElementProps>(
  ({ classes, label, url, loading }) => (
    <Grid item xs={6} md={4} lg={3}>
      <Card>
        <Link to={url} className={classes.link}>
          <CardContent>
            {loading ? (
              <Typography variant={"button"}>
                <Skeleton style={{ width: "80%" }} />
              </Typography>
            ) : (
              <Typography variant={"button"}>{label}</Typography>
            )}
          </CardContent>
        </Link>
      </Card>
    </Grid>
  )
);
