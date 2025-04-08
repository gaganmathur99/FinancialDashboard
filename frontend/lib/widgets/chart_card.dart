import 'package:flutter/material.dart';
import 'package:syncfusion_flutter_charts/charts.dart';

enum ChartType { pie, bar, line }

class ChartCard extends StatelessWidget {
  final String title;
  final String? subtitle;
  final Widget chart;
  final ChartType chartType;
  final List<ChartLegendItem>? legendItems;
  final VoidCallback? onTap;

  const ChartCard({
    Key? key,
    required this.title,
    this.subtitle,
    required this.chart,
    required this.chartType,
    this.legendItems,
    this.onTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Chart title and subtitle
              Text(
                title,
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              if (subtitle != null) ...[
                SizedBox(height: 4),
                Text(
                  subtitle!,
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.grey[600],
                  ),
                ),
              ],
              SizedBox(height: 16),
              
              // Chart widget
              SizedBox(
                height: 200,
                width: double.infinity,
                child: chart,
              ),
              
              // Legend (if provided)
              if (legendItems != null && legendItems!.isNotEmpty) ...[
                SizedBox(height: 16),
                ChartLegend(items: legendItems!),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class ChartLegendItem {
  final String label;
  final Color color;

  ChartLegendItem({required this.label, required this.color});
}

class ChartLegend extends StatelessWidget {
  final List<ChartLegendItem> items;

  const ChartLegend({
    Key? key,
    required this.items,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 16,
      runSpacing: 8,
      children: items.map((item) {
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 12,
              height: 12,
              decoration: BoxDecoration(
                color: item.color,
                shape: BoxShape.circle,
              ),
            ),
            SizedBox(width: 6),
            Text(
              item.label,
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey[700],
              ),
            ),
          ],
        );
      }).toList(),
    );
  }
}

// Data class for pie chart
class PieChartData {
  final String category;
  final double value;
  final Color color;

  PieChartData({required this.category, required this.value, required this.color});
}

class PieChartSample extends StatelessWidget {
  final List<PieChartData> chartData;

  const PieChartSample({
    Key? key,
    required this.chartData,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // No need to convert data, using Syncfusion chart data directly

    return SfCircularChart(
      series: <CircularSeries>[
        PieSeries<PieChartData, String>(
          dataSource: chartData,
          pointColorMapper: (PieChartData data, _) => data.color,
          xValueMapper: (PieChartData data, _) => data.category,
          yValueMapper: (PieChartData data, _) => data.value,
          radius: '80%',
        )
      ],
    );
  }
}

// Data class for bar chart
class BarChartData {
  final String category;
  final double value;
  final Color color;

  BarChartData({required this.category, required this.value, required this.color});
}

class BarChartSample extends StatelessWidget {
  final List<BarChartData> chartData;
  final double? maxY;

  const BarChartSample({
    Key? key,
    required this.chartData,
    this.maxY,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // No need to convert data, using Syncfusion chart data directly

    return SfCartesianChart(
      primaryXAxis: CategoryAxis(
        title: AxisTitle(text: 'Category'),
      ),
      primaryYAxis: NumericAxis(
        title: AxisTitle(text: 'Value'),
        maximum: maxY,
      ),
      series: <CartesianSeries>[
        ColumnSeries<BarChartData, String>(
          dataSource: chartData,
          xValueMapper: (BarChartData data, _) => data.category,
          yValueMapper: (BarChartData data, _) => data.value,
          pointColorMapper: (BarChartData data, _) => data.color,
          borderRadius: BorderRadius.circular(4),
        )
      ],
      tooltipBehavior: TooltipBehavior(enable: true),
    );
  }
}

// Data class for line chart
class LineChartData {
  final String xValue;
  final double yValue;
  final int seriesIndex;

  LineChartData({required this.xValue, required this.yValue, required this.seriesIndex});
}

class LineChartSample extends StatelessWidget {
  final List<LineChartData> chartData;
  final double? maxY;
  final String? leftTitle;
  final String? bottomTitle;
  final bool showDots;
  final List<Color> colors;

  const LineChartSample({
    Key? key,
    required this.chartData,
    this.maxY,
    this.leftTitle,
    this.bottomTitle,
    this.showDots = false,
    this.colors = const [Colors.blue],
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // No need to convert data, using Syncfusion chart data directly
    return SfCartesianChart(
      primaryXAxis: CategoryAxis(
        title: AxisTitle(text: bottomTitle ?? ''),
      ),
      primaryYAxis: NumericAxis(
        title: AxisTitle(text: leftTitle ?? ''),
        maximum: maxY,
      ),
      legend: Legend(isVisible: colors.length > 1),
      tooltipBehavior: TooltipBehavior(enable: true),
      series: _buildSeries(chartData, colors),
    );
  }
  
  List<CartesianSeries> _buildSeries(List<LineChartData> allData, List<Color> colors) {
    // Group data by series index
    Map<int, List<LineChartData>> seriesData = {};
    for (var data in allData) {
      if (!seriesData.containsKey(data.seriesIndex)) {
        seriesData[data.seriesIndex] = [];
      }
      seriesData[data.seriesIndex]!.add(data);
    }
    
    // Create a series for each line
    List<CartesianSeries> result = [];
    seriesData.forEach((index, data) {
      result.add(
        LineSeries<LineChartData, String>(
          dataSource: data,
          xValueMapper: (LineChartData data, _) => data.xValue,
          yValueMapper: (LineChartData data, _) => data.yValue,
          name: 'Series ${index + 1}',
          color: index < colors.length ? colors[index] : Colors.blue,
          markerSettings: MarkerSettings(
            isVisible: showDots,
            shape: DataMarkerType.circle,
            height: 7,
            width: 7,
          ),
        ),
      );
    });
    
    return result;
  }
}