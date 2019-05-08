import * as cubejs from '@cubejs-client/core';
import { QueryRenderer } from '@cubejs-client/react';
import Card from "@material-ui/core/Card";
import { Axis, Chart, Coord, Geom, Legend, Tooltip } from 'bizcharts';
import * as moment from 'moment';
import * as numeral from 'numeral';
import * as React from "react";

import CardTitle from "../../components/CardTitle";
import Skeleton from "../../components/Skeleton";

const CHART_HEIGHT = 400;
const API_KEY = 'd242612162ecbe8c2436d47d74b83ecc1640f690ef73aef1ccfd26cf6b887bc2';
const API_URL = 'https://cubejs-analytics.herokuapp.com/cubejs-api/v1';
const cubejsApi = cubejs(API_KEY, { apiUrl: API_URL });

const formatters = {
  currency: (val) => numeral(val).format('$0,0'),
  date: (val) => moment(val).format("MMM DD"),
  undefined: (val) => val
}
const renderLine = (resultSet) => (
  <Chart
    scale={{ category: { tickCount: 8 } }}
    height={CHART_HEIGHT}
    data={resultSet.chartPivot()}
    forceFit
  >
      <Axis name="category" label={{ formatter: formatters.date }} />
      {resultSet.seriesNames().map(s => (<Axis name={s.key} label={{ formatter: formatters[resultSet.loadResponse.annotation.measures[s.key].format] }} />))}
      <Tooltip crosshairs={{type : 'y'}} />
      {resultSet.seriesNames().map(s => (<Geom type="line" position={`category*${s.key}`} size={2} />))}
  </Chart>
);

const renderPie = (resultSet) => (
  <Chart height={CHART_HEIGHT} data={resultSet.chartPivot()} forceFit>
    <Coord type="theta" radius={0.75} />
    {resultSet.seriesNames().map(s => (<Axis name={s.key} />))}
    <Legend position="right" name="category" />
    <Tooltip showTitle={false} />
    {resultSet.seriesNames().map(s => (<Geom type="intervalStack" position={s.key} color="x" />))}
  </Chart>
);

const renderChart = (resultSet, visualizationType) => (
  {
    'line': renderLine,
    'pie': renderPie
  }[visualizationType](resultSet)
);

const ChartCard = ({ title, query, visualizationType }) => (
  <Card>
    <CardTitle title={title} />
    <QueryRenderer
      query={query}
      cubejsApi={cubejsApi}
      render={ ({ resultSet }) => {
        if (!resultSet) {
          return (
            <div style={{ padding: "10px" }}>
              <Skeleton />
            </div>
          )
        }

        return renderChart(resultSet, visualizationType);
      }}
    />
  </Card>
);

ChartCard.displayName = "ChartCard";
export default ChartCard;
