import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:shared_preferences/shared_preferences.dart';

DateTime _normalizeDateForNotes(DateTime date) =>
    DateTime(date.year, date.month, date.day);

class NotesPage extends StatefulWidget {
  const NotesPage({super.key});

  @override
  State<NotesPage> createState() => _NotesPageState();
}

class _NotesPageState extends State<NotesPage> {
  late DateTime _selectedDate;
  final TextEditingController _controller = TextEditingController();
  final Map<DateTime, String> _notesByDate = {};
  bool _isSaving = false;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _selectedDate = DateTime.now();
    _loadNotesFromStorage();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _onChangeSelectedDate(DateTime newDate) {
    final normalized = _normalizeDateForNotes(newDate);
    if (_normalizeDateForNotes(_selectedDate) == normalized) return;
    setState(() {
      _selectedDate = normalized;
      _syncController();
    });
  }

  void _syncController() {
    final normalized = _normalizeDateForNotes(_selectedDate);
    _controller.text = _notesByDate[normalized] ?? '';
  }

  void _onNoteChanged(String value) {
    final normalized = _normalizeDateForNotes(_selectedDate);
    setState(() {
      _notesByDate[normalized] = value;
      _isSaving = true;
    });

    Future.delayed(const Duration(milliseconds: 700), () {
      if (!mounted) return;
      _saveNotesToStorage().then((_) {
        if (!mounted) return;
        setState(() {
          _isSaving = false;
        });
      });
    });
  }

  Future<void> _loadNotesFromStorage() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString('notes_v1');
    if (raw == null) {
      setState(() {
        _isLoading = false;
      });
      _syncController();
      return;
    }

    try {
      final decoded = jsonDecode(raw) as Map<String, dynamic>;
      final map = <DateTime, String>{};
      decoded.forEach((key, value) {
        try {
          final date = DateTime.parse(key);
          if (value is String) {
            map[_normalizeDateForNotes(date)] = value;
          }
        } catch (_) {
          // Bozuk entry'leri yoksay
        }
      });

      setState(() {
        _notesByDate
          ..clear()
          ..addAll(map);
        _isLoading = false;
      });
      _syncController();
    } catch (_) {
      setState(() {
        _isLoading = false;
      });
      _syncController();
    }
  }

  Future<void> _saveNotesToStorage() async {
    final prefs = await SharedPreferences.getInstance();
    final data = <String, String>{};
    for (final entry in _notesByDate.entries) {
      final text = entry.value.trim();
      if (text.isNotEmpty) {
        final key = entry.key.toIso8601String().split('T').first;
        data[key] = text;
      }
    }
    await prefs.setString('notes_v1', jsonEncode(data));
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Notlar'),
      ),
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Color(0xFF111827),
              Color(0xFF020617),
            ],
          ),
        ),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 12),
            child: _isLoading
                ? const Center(
                    child: CircularProgressIndicator.adaptive(),
                  )
                : Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _NotesHeader(
                        selectedDate: _selectedDate,
                        onChangeDate: _onChangeSelectedDate,
                      ),
                      const SizedBox(height: 16),
                      _NotesEditorCard(
                        controller: _controller,
                        isSaving: _isSaving,
                        onChanged: _onNoteChanged,
                      ),
                    ],
                  ),
          ),
        ),
      ),
    );
  }
}

class _NotesHeader extends StatelessWidget {
  const _NotesHeader({
    required this.selectedDate,
    required this.onChangeDate,
  });

  final DateTime selectedDate;
  final ValueChanged<DateTime> onChangeDate;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final normalized = _normalizeDateForNotes(selectedDate);
    final subtitle =
        '${_weekdayLabel(normalized.weekday)}, ${normalized.day.toString().padLeft(2, '0')} ${_monthLabel(normalized.month)} ${normalized.year}';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Günlük Notlar',
          style: theme.textTheme.headlineSmall?.copyWith(
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          'Her gün için ayrı bir not alanın var. Tarihi değiştirerek geçmiş günlerin notlarına dönebilirsin.',
          style: theme.textTheme.bodySmall?.copyWith(
            color: Colors.white.withOpacity(0.7),
          ),
        ),
        const SizedBox(height: 16),
        _NotesDateBar(
          selectedDate: normalized,
          onChangeDate: onChangeDate,
          subtitle: subtitle,
        ),
      ],
    );
  }
}

class _NotesDateBar extends StatelessWidget {
  const _NotesDateBar({
    required this.selectedDate,
    required this.onChangeDate,
    required this.subtitle,
  });

  final DateTime selectedDate;
  final ValueChanged<DateTime> onChangeDate;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Row(
      children: [
        IconButton(
          tooltip: 'Bir gün geri',
          icon: const Icon(Icons.chevron_left_rounded),
          onPressed: () => onChangeDate(
            selectedDate.subtract(const Duration(days: 1)),
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
                initialDate: selectedDate,
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
                  'Seçili gün',
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
            selectedDate.add(const Duration(days: 1)),
          ),
        ),
      ],
    );
  }
}

class _NotesEditorCard extends StatelessWidget {
  const _NotesEditorCard({
    required this.controller,
    required this.isSaving,
    required this.onChanged,
  });

  final TextEditingController controller;
  final bool isSaving;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Expanded(
      child: ClipRRect(
        borderRadius: BorderRadius.circular(24),
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(24),
            border: Border.all(
              color: Colors.white.withOpacity(0.14),
            ),
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                Color(0xFF0B1120),
                Color(0xFF020617),
              ],
            ),
          ),
          padding: const EdgeInsets.fromLTRB(18, 14, 18, 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(
                    Icons.edit_note_rounded,
                    color: Color(0xFF38BDF8),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Bugünün notu',
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          'Düşüncelerini, kararlarını ve aksiyon maddelerini buraya yaz.',
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: Colors.white.withOpacity(0.65),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.04),
                      borderRadius: BorderRadius.circular(999),
                    ),
                    child: Row(
                      children: [
                        Container(
                          width: 6,
                          height: 6,
                          decoration: const BoxDecoration(
                            color: Color(0xFF22C55E),
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 6),
                        Text(
                          'Otomatik kaydediliyor',
                          style: theme.textTheme.labelSmall?.copyWith(
                            color: Colors.white.withOpacity(0.7),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const Spacer(),
                  AnimatedOpacity(
                    duration: const Duration(milliseconds: 200),
                    opacity: isSaving ? 1 : 0.0,
                    child: Row(
                      children: [
                        const SizedBox(
                          width: 14,
                          height: 14,
                          child: CircularProgressIndicator(
                            strokeWidth: 1.6,
                            color: Color(0xFF38BDF8),
                          ),
                        ),
                        const SizedBox(width: 6),
                        Text(
                          'Kaydediliyor...',
                          style: theme.textTheme.labelSmall?.copyWith(
                            color: Colors.white.withOpacity(0.8),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Expanded(
                child: Container(
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(18),
                    color: Colors.black.withOpacity(0.35),
                    border: Border.all(
                      color: Colors.white.withOpacity(0.08),
                    ),
                  ),
                  padding: const EdgeInsets.symmetric(
                      horizontal: 12, vertical: 8),
                  child: TextField(
                    controller: controller,
                    onChanged: onChanged,
                    maxLines: null,
                    expands: true,
                    keyboardType: TextInputType.multiline,
                    style: GoogleFonts.inter(
                      textStyle: theme.textTheme.bodyMedium?.copyWith(
                        height: 1.45,
                      ),
                    ),
                    decoration: InputDecoration(
                      hintText:
                          'Bugüne dair önemli notlarını, kararlarını ve aksiyon maddelerini buraya yaz...',
                      hintStyle: theme.textTheme.bodyMedium?.copyWith(
                        color: Colors.white.withOpacity(0.45),
                      ),
                      border: InputBorder.none,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _IconCircleButton extends StatelessWidget {
  const _IconCircleButton({
    required this.icon,
    required this.onTap,
  });

  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: Colors.black.withOpacity(0.45),
          border: Border.all(
            color: Colors.white.withOpacity(0.3),
          ),
        ),
        padding: const EdgeInsets.all(4),
        child: Icon(
          icon,
          size: 18,
          color: Colors.white,
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

