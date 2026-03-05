import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import 'notes_page.dart';
import 'overview_placeholder.dart';
import 'config.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';
import 'package:pdfx/pdfx.dart';
import 'package:universal_io/io.dart';

DateTime _normalizeDate(DateTime date) =>
    DateTime(date.year, date.month, date.day);

void main() {
  runApp(const AhtabyteApp());
}

class AhtabyteApp extends StatelessWidget {
  const AhtabyteApp({super.key});

  @override
  Widget build(BuildContext context) {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: const Color(0xFF6750A4),
      brightness: Brightness.dark,
    );

    return MaterialApp(
      title: 'Günlük Raporlar',
      debugShowCheckedModeBanner: false,
      themeMode: ThemeMode.dark,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: colorScheme,
        scaffoldBackgroundColor: const Color(0xFF050816),
        textTheme: GoogleFonts.interTextTheme(
          ThemeData.dark().textTheme,
        ),
        appBarTheme: AppBarTheme(
          elevation: 0,
          centerTitle: false,
          backgroundColor: Colors.transparent,
          foregroundColor: colorScheme.onBackground,
          titleTextStyle: GoogleFonts.inter(
            fontSize: 22,
            fontWeight: FontWeight.w700,
            letterSpacing: 0.2,
          ),
        ),
      ),
      home: const _RootShell(),
    );
  }
}

class _RootShell extends StatefulWidget {
  const _RootShell({super.key});

  @override
  State<_RootShell> createState() => _RootShellState();
}

class _RootShellState extends State<_RootShell> {
  int _selectedIndex = 0;

  late final List<Widget> _pages = const [
    DailyReportViewerPage(),
    NotesPage(),
    OverviewPlaceholderPage(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _selectedIndex,
        children: _pages,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (index) {
          setState(() {
            _selectedIndex = index;
          });
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.picture_as_pdf_outlined),
            selectedIcon: Icon(Icons.picture_as_pdf_rounded),
            label: 'Raporlar',
          ),
          NavigationDestination(
            icon: Icon(Icons.edit_note_outlined),
            selectedIcon: Icon(Icons.edit_note_rounded),
            label: 'Notlar',
          ),
          NavigationDestination(
            icon: Icon(Icons.dashboard_customize_outlined),
            selectedIcon: Icon(Icons.dashboard_customize_rounded),
            label: 'Genel Bakış',
          ),
        ],
      ),
    );
  }
}

class DailyReport {
  DailyReport({
    required this.date,
    required this.title,
  });

  final DateTime date;
  final String title;
}

enum ReportStatus {
  available,
  notFound,
  error,
}

class DailyReportViewerPage extends StatefulWidget {
  const DailyReportViewerPage({super.key});

  @override
  State<DailyReportViewerPage> createState() => _DailyReportViewerPageState();
}

class _DailyReportViewerPageState extends State<DailyReportViewerPage> {
  late DateTime _selectedDate;
  final Map<DateTime, ReportStatus> _reportStatusByDate = {};
  PdfControllerPinch? _pdfController;
  bool _isPdfLoading = false;
  String? _pdfError;

  static const String _basePdfPath = '/report';

  String get _basePdfUrl => '${Config.baseUrl}$_basePdfPath';

  @override
  void initState() {
    super.initState();

    _selectedDate = DateTime.now();

    _loadPdfForSelectedDate();
  }

  @override
  void dispose() {
    _pdfController?.dispose();
    super.dispose();
  }

  void _onChangeSelectedDate(DateTime newDate) {
    final normalized = _normalizeDate(newDate);
    if (_normalizeDate(_selectedDate) == normalized) return;
    setState(() {
      _selectedDate = normalized;
      _loadPdfForSelectedDate();
    });
  }

  String _formatDateForApi(DateTime date) {
    final year = date.year.toString().padLeft(4, '0');
    final month = date.month.toString().padLeft(2, '0');
    final day = date.day.toString().padLeft(2, '0');
    return '$year-$month-$day';
  }

  Future<void> _loadPdfForSelectedDate() async {
    final date = _selectedDate;
    final normalizedDate = _normalizeDate(date);
    final dateString = _formatDateForApi(date);
    final url = '$_basePdfUrl/$dateString';

    _pdfController?.dispose();
    setState(() {
      _pdfController = null;
      _isPdfLoading = true;
      _pdfError = null;
    });

    try {
      // Web'de basitçe network'ten, mobil/desktop'ta önce cache'e bak.
      if (!kIsWeb) {
        final docsDir = await getApplicationDocumentsDirectory();
        final reportsDir = Directory('${docsDir.path}/reports');
        if (!await reportsDir.exists()) {
          await reportsDir.create(recursive: true);
        }
        final fileName = 'report_$dateString.pdf';
        final filePath = '${reportsDir.path}/$fileName';
        final file = File(filePath);

        if (await file.exists()) {
          final documentFuture = PdfDocument.openFile(filePath);
          setState(() {
            _pdfController = PdfControllerPinch(document: documentFuture);
            _isPdfLoading = false;
          });
          return;
        }
      }

      final response = await http.get(Uri.parse(url));
      if (response.statusCode == 200) {
        if (!kIsWeb) {
          final docsDir = await getApplicationDocumentsDirectory();
          final reportsDir = Directory('${docsDir.path}/reports');
          if (!await reportsDir.exists()) {
            await reportsDir.create(recursive: true);
          }
          final fileName = 'report_$dateString.pdf';
          final filePath = '${reportsDir.path}/$fileName';
          final file = File(filePath);
          await file.writeAsBytes(response.bodyBytes, flush: true);
        }

        final documentFuture = PdfDocument.openData(response.bodyBytes);
        setState(() {
          _pdfController = PdfControllerPinch(document: documentFuture);
          _isPdfLoading = false;
          _reportStatusByDate[normalizedDate] = ReportStatus.available;
        });
      } else {
        setState(() {
          _pdfError =
              'Bu tarih için rapor bulunamadı. (HTTP ${response.statusCode})';
          _isPdfLoading = false;
          _reportStatusByDate[normalizedDate] = ReportStatus.notFound;
        });
      }
    } catch (e) {
      setState(() {
        _pdfError = 'Rapor yüklenirken bir hata oluştu.';
        _isPdfLoading = false;
        _reportStatusByDate[normalizedDate] = ReportStatus.error;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // Mobil için daha tutarlı görünüm
      extendBodyBehindAppBar: false,
      appBar: AppBar(
        title: const Text('Günlük Raporlar'),
      ),
      body: Stack(
        children: [
          _GradientBackground(),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _HeaderSection(selectedDate: _selectedDate),
                  const SizedBox(height: 12),
                  _SimpleDateBar(
                    selectedDate: _selectedDate,
                    onChangeDate: _onChangeSelectedDate,
                  ),
                  const SizedBox(height: 16),
                  Expanded(
                    child: _MainContentLayout(
                      pdfController: _pdfController,
                      isPdfLoading: _isPdfLoading,
                      pdfError: _pdfError,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _GradientBackground extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Color(0xFF16162E),
            Color(0xFF020617),
          ],
        ),
      ),
    );
  }
}

class _HeaderSection extends StatelessWidget {
  const _HeaderSection({required this.selectedDate});

  final DateTime selectedDate;

  @override
  Widget build(BuildContext context) {
    final date = selectedDate;
    final subtitle =
        '${_weekdayLabel(date.weekday)}, ${date.day.toString().padLeft(2, '0')} ${_monthLabel(date.month)}';

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Rapor Özeti',
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    color: Colors.white.withOpacity(0.7),
                    letterSpacing: 0.3,
                  ),
            ),
            const SizedBox(height: 4),
            Text(
              subtitle,
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
            ),
          ],
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(999),
            color: Colors.white.withOpacity(0.06),
            border: Border.all(
              color: Colors.white.withOpacity(0.12),
            ),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                Icons.cloud_done_rounded,
                size: 16,
                color: Colors.greenAccent.shade200,
              ),
              const SizedBox(width: 6),
              Text(
                'Senkronize',
                style: Theme.of(context).textTheme.labelMedium?.copyWith(
                      color: Colors.white.withOpacity(0.85),
                    ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _SimpleDateBar extends StatelessWidget {
  const _SimpleDateBar({
    required this.selectedDate,
    required this.onChangeDate,
  });

  final DateTime selectedDate;
  final ValueChanged<DateTime> onChangeDate;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final normalized = _normalizeDate(selectedDate);
    final subtitle =
        '${_weekdayLabel(normalized.weekday)}, ${normalized.day.toString().padLeft(2, '0')} ${_monthLabel(normalized.month)} ${normalized.year}';

    return Row(
      children: [
        IconButton(
          tooltip: 'Bir gün geri',
          icon: const Icon(Icons.chevron_left_rounded),
          onPressed: () => onChangeDate(
            normalized.subtract(const Duration(days: 1)),
          ),
        ),
        Expanded(
          child: FilledButton.tonalIcon(
            style: FilledButton.styleFrom(
              padding:
                  const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(999),
              ),
            ),
            onPressed: () async {
              final picked = await showDatePicker(
                context: context,
                initialDate: normalized,
                firstDate: DateTime(2020, 1, 1),
                lastDate: DateTime.now().add(const Duration(days: 365)),
              );
              if (picked != null) {
                onChangeDate(picked);
              }
            },
            icon: const Icon(Icons.calendar_today_rounded, size: 18),
            label: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  'Seçili tarih',
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: Colors.white.withOpacity(0.85),
                  ),
                ),
                Text(
                  subtitle,
                  style: theme.textTheme.labelMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ),
        IconButton(
          tooltip: 'Bir gün ileri',
          icon: const Icon(Icons.chevron_right_rounded),
          onPressed: () => onChangeDate(
            normalized.add(const Duration(days: 1)),
          ),
        ),
      ],
    );
  }
}

class _MainContentLayout extends StatelessWidget {
  const _MainContentLayout({
    required this.pdfController,
    required this.isPdfLoading,
    required this.pdfError,
  });

  final PdfControllerPinch? pdfController;
  final bool isPdfLoading;
  final String? pdfError;

  @override
  Widget build(BuildContext context) {
    final isWide =
        MediaQuery.of(context).size.width > 720; // tablet / landscape için

    if (isWide) {
      return _PdfCard(
        controller: pdfController,
        isLoading: isPdfLoading,
        error: pdfError,
        onRetry: () => _onRetry(context),
      );
    }

    return _PdfCard(
      controller: pdfController,
      isLoading: isPdfLoading,
      error: pdfError,
      onRetry: () => _onRetry(context),
    );
  }

  void _onRetry(BuildContext context) {
    final state =
        context.findAncestorStateOfType<_DailyReportViewerPageState>();
    state?._loadPdfForSelectedDate();
  }
}

class _PdfCard extends StatelessWidget {
  const _PdfCard({
    required this.controller,
    required this.isLoading,
    required this.error,
    required this.onRetry,
  });

  final PdfControllerPinch? controller;
  final bool isLoading;
  final String? error;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(24),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.04),
          borderRadius: BorderRadius.circular(24),
          border: Border.all(
            color: Colors.white.withOpacity(0.12),
          ),
        ),
        child: Stack(
          children: [
            if (controller != null)
              PdfViewPinch(
                controller: controller!,
                backgroundDecoration: const BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [
                      Color(0xFF020617),
                      Color(0xFF020617),
                    ],
                  ),
                ),
              )
            else if (isLoading)
              const Center(
                child: CircularProgressIndicator.adaptive(),
              )
            else if (error != null)
              Center(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 24),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(
                        Icons.picture_as_pdf_rounded,
                        color: Color(0xFFF97316),
                        size: 32,
                      ),
                      const SizedBox(height: 12),
                      Text(
                        error!,
                        textAlign: TextAlign.center,
                        style: Theme.of(context)
                            .textTheme
                            .bodyMedium
                            ?.copyWith(color: Colors.white.withOpacity(0.85)),
                      ),
                      const SizedBox(height: 12),
                      TextButton.icon(
                        onPressed: onRetry,
                        style: TextButton.styleFrom(
                          foregroundColor: Colors.white,
                          backgroundColor: Colors.white.withOpacity(0.08),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(999),
                          ),
                        ),
                        icon: const Icon(Icons.refresh_rounded),
                        label: const Text('Tekrar dene'),
                      ),
                    ],
                  ),
                ),
              ),
            Positioned(
              left: 16,
              right: 16,
              bottom: 16,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  _PdfNavButton(
                    icon: Icons.chevron_left_rounded,
                    onTap: controller == null
                        ? null
                        : () => controller!.previousPage(
                              duration: const Duration(milliseconds: 220),
                              curve: Curves.easeOutCubic,
                            ),
                  ),
                  _PdfNavButton(
                    icon: Icons.chevron_right_rounded,
                    onTap: controller == null
                        ? null
                        : () => controller!.nextPage(
                              duration: const Duration(milliseconds: 220),
                              curve: Curves.easeOutCubic,
                            ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PdfNavButton extends StatelessWidget {
  const _PdfNavButton({
    required this.icon,
    required this.onTap,
  });

  final IconData icon;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final isDisabled = onTap == null;

    return GestureDetector(
      onTap: isDisabled ? null : onTap,
      child: AnimatedOpacity(
        duration: const Duration(milliseconds: 180),
        opacity: isDisabled ? 0.4 : 1,
        child: Container(
          decoration: BoxDecoration(
            color: Colors.black.withOpacity(0.45),
            borderRadius: BorderRadius.circular(999),
            border: Border.all(
              color: Colors.white.withOpacity(0.3),
            ),
          ),
          padding: const EdgeInsets.all(8),
          child: Icon(
            icon,
            size: 24,
            color: Colors.white,
          ),
        ),
      ),
    );
  }
}

String _weekdayLabel(int weekday) {
  switch (weekday) {
    case DateTime.monday:
      return 'Pazartesi';
    case DateTime.tuesday:
      return 'Salı';
    case DateTime.wednesday:
      return 'Çarşamba';
    case DateTime.thursday:
      return 'Perşembe';
    case DateTime.friday:
      return 'Cuma';
    case DateTime.saturday:
      return 'Cumartesi';
    case DateTime.sunday:
      return 'Pazar';
    default:
      return '';
  }
}

String _shortWeekdayLabel(int weekday) {
  switch (weekday) {
    case DateTime.monday:
      return 'Pzt';
    case DateTime.tuesday:
      return 'Sal';
    case DateTime.wednesday:
      return 'Çar';
    case DateTime.thursday:
      return 'Per';
    case DateTime.friday:
      return 'Cum';
    case DateTime.saturday:
      return 'Cmt';
    case DateTime.sunday:
      return 'Paz';
    default:
      return '';
  }
}

String _monthLabel(int month) {
  switch (month) {
    case 1:
      return 'Ocak';
    case 2:
      return 'Şubat';
    case 3:
      return 'Mart';
    case 4:
      return 'Nisan';
    case 5:
      return 'Mayıs';
    case 6:
      return 'Haziran';
    case 7:
      return 'Temmuz';
    case 8:
      return 'Ağustos';
    case 9:
      return 'Eylül';
    case 10:
      return 'Ekim';
    case 11:
      return 'Kasım';
    case 12:
      return 'Aralık';
    default:
      return '';
  }
}

String _shortMonthLabel(int month) {
  switch (month) {
    case 1:
      return 'Oca';
    case 2:
      return 'Şub';
    case 3:
      return 'Mar';
    case 4:
      return 'Nis';
    case 5:
      return 'May';
    case 6:
      return 'Haz';
    case 7:
      return 'Tem';
    case 8:
      return 'Ağu';
    case 9:
      return 'Eyl';
    case 10:
      return 'Eki';
    case 11:
      return 'Kas';
    case 12:
      return 'Ara';
    default:
      return '';
  }
}

