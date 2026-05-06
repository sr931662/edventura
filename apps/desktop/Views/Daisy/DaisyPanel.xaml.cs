using edventura_desktop.ViewModels;
using System;
using System.ComponentModel;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Threading;

namespace edventura_desktop.Views.Daisy
{
    public partial class DaisyPanel : UserControl
    {
        private DaisyViewModel? _vm;
        private DispatcherTimer? _dotTimer;
        private int _dotStep = 0;

        public DaisyPanel()
        {
            InitializeComponent();
            DataContextChanged += OnDataContextChanged;
            Loaded += (_, _) => InitDotAnimation();
        }

        // ── DataContext wiring ─────────────────────────────────────────────

        private void OnDataContextChanged(object sender, DependencyPropertyChangedEventArgs e)
        {
            if (_vm != null)
            {
                _vm.PropertyChanged -= OnVmPropertyChanged;
                _vm.ScrollToBottomRequested -= ScrollToBottom;
            }

            _vm = DataContext as DaisyViewModel;

            if (_vm != null)
            {
                _vm.PropertyChanged += OnVmPropertyChanged;
                _vm.ScrollToBottomRequested += ScrollToBottom;
            }
        }

        private void OnVmPropertyChanged(object? sender, PropertyChangedEventArgs e)
        {
            if (e.PropertyName == nameof(DaisyViewModel.IsOpen))
            {
                if (_vm!.IsOpen) AnimateOpen();
                else AnimateClose();
            }
            else if (e.PropertyName == nameof(DaisyViewModel.IsThinking))
            {
                if (_vm!.IsThinking) _dotTimer?.Start();
                else _dotTimer?.Stop();
            }
        }

        // ── Slide animations ───────────────────────────────────────────────

        public void AnimateOpen()
        {
            Visibility = Visibility.Visible;
            var ease = new CubicEase { EasingMode = EasingMode.EaseOut };
            var anim = new DoubleAnimation(400, 0, new Duration(TimeSpan.FromSeconds(0.32)))
            {
                EasingFunction = ease
            };
            PanelSlide.BeginAnimation(TranslateTransform.XProperty, anim);
            InputBox.Focus();
        }

        public void AnimateClose()
        {
            var ease = new CubicEase { EasingMode = EasingMode.EaseIn };
            var anim = new DoubleAnimation(0, 400, new Duration(TimeSpan.FromSeconds(0.25)))
            {
                EasingFunction = ease
            };
            anim.Completed += (_, _) => Visibility = Visibility.Collapsed;
            PanelSlide.BeginAnimation(TranslateTransform.XProperty, anim);
        }

        // ── Thinking dots animation (DispatcherTimer based) ───────────────

        private void InitDotAnimation()
        {
            _dotTimer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(280) };
            _dotTimer.Tick += (_, _) =>
            {
                _dotStep = (_dotStep + 1) % 3;
                Dot1.Opacity = _dotStep == 0 ? 1.0 : 0.3;
                Dot2.Opacity = _dotStep == 1 ? 1.0 : 0.3;
                Dot3.Opacity = _dotStep == 2 ? 1.0 : 0.3;
            };
        }

        // ── Auto-scroll ────────────────────────────────────────────────────

        private void ScrollToBottom()
        {
            Dispatcher.InvokeAsync(() =>
            {
                MessagesScroll.UpdateLayout();
                MessagesScroll.ScrollToEnd();
            }, DispatcherPriority.Loaded);
        }

        // ── UI events ─────────────────────────────────────────────────────

        private void BtnClose_Click(object sender, RoutedEventArgs e)
            => _vm?.CloseCommand.Execute(null);

        private void InputBox_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Enter && Keyboard.Modifiers == ModifierKeys.None)
            {
                e.Handled = true;
                _vm?.SendCommand.Execute(null);
            }
            // Shift+Enter → natural newline (TextBox handles it)
        }

        private void Chip_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button btn && btn.Tag is string prompt && _vm != null)
            {
                _vm.InputText = prompt;
                _vm.SendCommand.Execute(null);
            }
        }
    }
}